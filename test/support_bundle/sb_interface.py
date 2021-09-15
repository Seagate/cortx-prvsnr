import os
import sys
import argparse
import subprocess
import tarfile
import time

from sb_config import PV_CLAIM_LIST, SB_FILE_PATH, SB_TAG


class SSPLBundleError(Exception):
    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize with custom error message and return code."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Format error string."""
        print("SSPLBundleError(%d): %s" %(self._rc, self._desc))

class SupportBundle:

    KUBECTL = "kubectl"
    def validate(self):
        self.check_shared_storageclass()
        self.check_sb_image()
        self.check_sb_pod_yaml_exists()

    def process(self):
        # Run the support-bundle pod to generate the cortx logs tar.
        cmd = f"{self.KUBECTL} apply -f sb-pod.yaml"
        _, _, rc = self._run_command(cmd)
        if rc != 0:
            msg = "Failed to deploy the supoort-bundle pod."
            raise SSPLBundleError(1, msg)
        time.sleep(10)
        if os.path.exists(SB_FILE_PATH):
            print(f"Support Bundle generated successfully at path:{SB_FILE_PATH} !!!")
        else:
            msg = "Cortx Logs tarfile is not generated at specified path."
            raise SSPLBundleError(1, msg)

    def untar_cortx_bundle(self):
        if os.path.exists(SB_FILE_PATH):
            tar = tarfile.open(SB_FILE_PATH, "r:gz")
            tar.extractall()
            tar.close()

    def check_shared_storageclass(self):
        for pvc in PV_CLAIM_LIST:
            cmd = f"{self.KUBECTL} get pvc | grep {pvc}"
            response, err, rc = self._run_command(cmd)
            if err:
                msg = f"Failed in Validating PV-claim:{pvc}. ERROR:{err}" 
                raise SSPLBundleError(1, msg)
            if "Bound" not in response:
                msg = f"PV-claim:{pvc} status is not Bound."
                raise SSPLBundleError(1, msg)

    def check_sb_image(self):
        cmd = "docker images | grep 'support_bundle' "
        response, _, _ = self._run_command(cmd)
        if not response:
            # Support_bundle image not present, build docker image
            cmd = f"docker build -f Dockerfile -t support_bundle:{SB_TAG} ."
            response, err, rc = self._run_command(cmd)
            if rc != 0:
                msg = f"Failed to build support-bundle image. ERROR:{err}"
                raise SSPLBundleError(1, msg)
            else:
                print("Building Support-bundle Image.")
                print(response)

    def check_sb_pod_yaml_exists(self):
        file_path = os.path.abspath("sb-pod.yaml")
        if not os.path.exists(file_path):
            msg = f"support bundle deployment yaml doesn't exist"
            raise SSPLBundleError(1, msg)

    def cleanup(self):
        cmd = f"{self.KUBECTL} delete pod sb-pod"
        _, _, rc = self._run_command(cmd)
        if rc != 0:
            msg = "Failed to delete the support-bundle pod"
            raise SSPLBundleError(1, msg)

    def _run_command(self, command):
        """Run the command and get the response and error returned"""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        return_code = process.wait()
        response, error = process.communicate()
        return response.rstrip('\n'), error.rstrip('\n'), return_code

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='''Bundle cortx logs ''')
        parser.add_argument('--generate', help='generate support bundle',
                            action='store_true')
        parser.add_argument('--untar', help='untar the created bundle',
                            action='store_true')
        args=parser.parse_args()
        return args

def main():
    args = SupportBundle.parse_args()
    if args.generate:
        SupportBundle().validate()
        SupportBundle().process()
        SupportBundle().cleanup()
    if args.untar:
        SupportBundle().untar_cortx_bundle()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)


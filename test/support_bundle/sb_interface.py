import os
import sys
import argparse
import subprocess
import shlex
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

class SupportBundleInterface:

    """ SupportBundle interface to generate a support bundle of cortx logs,
        in a containerised env.

        For example: python3 sb_interface.py --generate

    """
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

    @staticmethod
    def untar_cortx_bundle():
        if os.path.exists(SB_FILE_PATH):
            tar = tarfile.open(SB_FILE_PATH, "r:gz")
            tar.extractall()
            tar.close()

    def check_shared_storageclass(self):
        cmd = f"{self.KUBECTL} get pvc"
        response, err, _ = self._run_command(cmd)
        if err:
            msg = f"Failed in Validating PV-claim. ERROR:{err}"
            raise SSPLBundleError(1, msg)
        for pvc in PV_CLAIM_LIST:
            if pvc and "Bound" not in response:
                msg = f"Please check PV-Claim:{pvc} exists and in 'Bound' state."
                raise SSPLBundleError(1, msg)

    def check_sb_image(self):
        cmd = "docker images"
        response, _, _ = self._run_command(cmd)
        if "support_bundle" not in response:
            # Support_bundle image not present, build docker image
            cmd = f"docker build -f Dockerfile -t support_bundle:{SB_TAG} ."
            response, err, rc = self._run_command(cmd)
            if rc != 0:
                msg = f"Failed to build support-bundle image. ERROR:{err}"
                raise SSPLBundleError(1, msg)
            else:
                print("==== Building Support-bundle Image. ====")
                print(response)

    @staticmethod
    def check_sb_pod_yaml_exists():
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
        """Run the command and get the response and error returned."""
        cmd = shlex.split(command) if isinstance(command, str) else command
        process = subprocess.run(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=False)
        output = process.stdout.decode('UTF-8')
        error = process.stderr.decode('UTF-8')
        returncode = process.returncode
        return output, error, returncode

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
    args = SupportBundleInterface.parse_args()
    SupportBundleObj = SupportBundleInterface()
    if args.generate:
        SupportBundleObj.validate()
        SupportBundleObj.process()
        SupportBundleObj.cleanup()
    if args.untar:
        SupportBundleInterface.untar_cortx_bundle()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)


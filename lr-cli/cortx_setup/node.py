import argparse
import logging

from provisioner.commands import deploy
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)

cortx_components = dict(
    utils=[
        "cortx_utils"
    ],
    iopath=[
        "motr",
        "s3server",
        "hare"
    ],
    controlpath=[
        "sspl",
        "uds",
        "csm"
    ],
    ha=[
        "ha.cortx-ha"
    ]
)


class Node():

    """Configure node"""

    def initialize(self):

        """Initialize cortx components by calling post_install command"""

        node_id = local_minion_id()

        logger.info("Invoking post_install command for all cortx components")
        for component in cortx_components:
            states = cortx_components[component]
            for state in states:
                print("init called")
                try:
                    deploy.Deploy()._apply_state(
                        state, targets=node_id, stages=['config.post_install']
                    )
                except Exception as ex:
                    raise ex
        logger.info("Done")


def _parse_args():
    parser = argparse.ArgumentParser(description='Configure node')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    Node().initialize()

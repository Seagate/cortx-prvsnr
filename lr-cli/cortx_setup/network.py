import argparse
import logging

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)


class Network():

    """Configure network"""

    def config(self, transport_type=None, interface_type=None,
            network_type=None, interfaces=None
    ):
        """Update provided network details in pillar data"""

        node_id = local_minion_id()
        if transport_type is not None:
            logger.info("Updating transport type in pillar data")
            PillarSet().run(
                f'node_info/{node_id}/network/data/transport_type',
                f'{transport_type}',
                targets=node_id,
                local=True
            )

        if interface_type is not None:
            logger.info("Updating interface type in pillar data")
            PillarSet().run(
                f'node_info/{node_id}/network/data/interface_type',
                f'{interface_type}',
                targets=node_id,
                local=True
            )

        if network_type is not None:
            if interfaces is not None:
                logger.info(
                    f"Updating interfaces for {network_type} network "
                    "in pillar data"
                )
                PillarSet().run(
                    f'node_info/{node_id}/network/{network_type}/intefaces',
                    f'{interfaces}',
                    targets=node_id,
                    local=True
                )
            else:
                logger.error(
                    f"Interfaces should be provided for {network_type} network"
                )
        logger.info("Done")


def _parse_args():
    parser = argparse.ArgumentParser(description='Configure netowrk')
    parser.add_argument('--transport_type', type=str,
        help='Network transport type', default=None
    )
    parser.add_argument('--interface_type', type=str,
        help='Network interface type', default=None
    )
    parser.add_argument('--network_type', type=str,
        help='Network type if interfaces specified', default=None
    )
    parser.add_argument('--interfaces', type=str,
        help='List of interfaces', default=None
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    Network().config(args.transport_type, args.interface_type,
                args.network_type, args.interfaces
    )

import argparse
import logging

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)


class Network():

    """Configure network"""

    def config(self, transport_type=None, interface_type=None,
            network_type=None, interfaces=None, private=False
    ):
        """
        Update provided network details in pillar data

        :param trasport_type:
            (optional) Transport type for network e.g {lnet|libfabric}.
        :param interface_type:
            (optional) Interface type for network e.g {tcp|o2ib}.
        :param network_type:
            (optional) Network type for provided interfaces e.g {data|mgmt}.
        :param interfaces:
            (optional) List of interfaces for provided network_type
            e.g ['eth1', 'eth2'].
        :param private:
            (optional) Use provided interfaces for private network.
        """

        node_id = local_minion_id()
        if transport_type is not None:
            logger.info(
                f"Updating transport type to {transport_type} in pillar data"
            )
            PillarSet().run(
                f'cluster/{node_id}/network/data/transport_type',
                f'{transport_type}',
                targets=node_id,
                local=True
            )

        if interface_type is not None:
            logger.info(
                f"Updating interface type to {interface_type} in pillar data"
                )
            PillarSet().run(
                f'cluster/{node_id}/network/data/interface_type',
                f'{interface_type}',
                targets=node_id,
                local=True
            )

        if interfaces is not None:
            if network_type == 'data':
                print("ufudy")
                iface_key = (
                    'private_interfaces' if private else 'public_interfaces'
                )
                logger.info(
                    f"Updating {iface_key} for {network_type} network "
                    "in pillar data"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/{network_type}/{iface_key}',
                    f'{interfaces}',
                    targets=node_id,
                    local=True
                )
            elif network_type == 'mgmt':
                logger.info(
                    f"Updating interfaces for {network_type} network "
                    "in pllar data"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/{network_type}/interfaces',
                    f'{interfaces}',
                    targets=node_id,
                    local=True
                )
            else:
                logger.error(
                    "Network type should specified for provided interfaces"
                )

        logger.info("Done")


def _parse_args():
    parser = argparse.ArgumentParser(description='Configure network')
    parser.add_argument('--transport_type', type=str,
        help='Network transport type e.g {lnet|libfabric}', default=None
    )
    parser.add_argument('--interface_type', type=str,
        help='Network interface type e.g {tcp|o2ib}', default=None
    )
    parser.add_argument('--network_type', type=str,
        choices=['data', 'mgmt'], default=None,
        help='Network type if interfaces specified e.g {data|mgmt}'
    )
    parser.add_argument('--interfaces', type=str,
        help='List of interfaces e.g eth1, eth2', default=None,
        nargs='+'
    )
    parser.add_argument('--private',
        help='Use provided interfaces for private network', default=False,
        action='store_true'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    Network().config(args.transport_type, args.interface_type,
                args.network_type, args.interfaces, args.private
    )

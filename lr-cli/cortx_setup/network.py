import logging

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)

class Network():

    def config(transport_type = None, interface_type = None,
                network_type = None, interfaces = None
            ):
        node_id = local_minion_id()

        if transport_type:
            logger.info("Updating transport type in pillar data")
            PillarSet().run(
                f'cluster/{node_id}/network/data/transport_type',
                f'{transport_type}',
                targets=node_id,
                local=True
            )

        elif interface_type:
            logger.info("Updating interface type in pillar data")
            PillarSet().run(
                f'cluster/{node_id}/network/data/interface_type',
                f'{interface_type}',
                targets=node_id,
                local=True
            )

        elif network_type:
            if interfaces is not None:
                logger.info(f"Updating interfaces for {network_type} network in pillar data")
                PillarSet().run(
                    f'cluster/{node_id}/network/{network_type}/intefaces',
                    f'{interfaces}',
                    targets=node_id,
                    local=True
                )
            else:
                logger.error(f"Interfaces should be provided for {network_type} network")
        else:
            logger.error("Network details should be provided for configuration")

        logger.info('Done')

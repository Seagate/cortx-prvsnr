from provisioner import hare


def test_cluster_mgmt():
    hare.ensure_cluster_is_stopped()
    hare.ensure_cluster_is_started()

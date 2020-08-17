from provisioner import ssh


def test_keygen_input_checks(mocker):
    priv_key_path = 'some-path'
    comment = 'some-comment'
    passphrase = 'some-phrase'
    cmd = 'ssh-keygen -t rsa -b 4096 -o -a 100'

    run_m = mocker.patch.object(ssh, 'run_subprocess_cmd', autospec=True)

    ssh.keygen(priv_key_path)
    run_m.assert_called_with((cmd.split() + ['-C', '', '-N', '', '-f', str(priv_key_path)]), input='y')

    ssh.keygen(priv_key_path, comment=comment)
    run_m.assert_called_with((cmd.split() + ['-C', comment, '-N', '', '-f', str(priv_key_path)]), input='y')

    ssh.keygen(priv_key_path, passphrase=passphrase)
    run_m.assert_called_with((cmd.split() + ['-C', '', '-N', passphrase, '-f', str(priv_key_path)]), input='y')

    ssh.keygen(priv_key_path, comment=comment, passphrase=passphrase)
    run_m.assert_called_with((cmd.split() + ['-C', comment, '-N', passphrase, '-f', str(priv_key_path)]), input='y')


# def test_keygen_output_check(mocker):
#     priv_key_path = 'some-path'
#     comment = 'some-comment'
#     passphrase = 'some-phrase'
#     ret_val = 'some-ret-val'
#
#     mocker.patch.object(utils, 'run_subprocess_cmd', autospec=True, return_value=ret_val)
#
#     assert ssh.keygen(priv_key_path, comment, passphrase) == ret_val


def test_copy_id_input_checks(mocker):
    host = 'some-host'
    user = 'some-user'
    port = 1234
    priv_key_path = 'some-path'
    ssh_options = ['option1', 'option2']
    copy_id_cmd = 'ssh-copy-id'

    run_m = mocker.patch.object(ssh, 'run_subprocess_cmd', autospec=True)

    ssh.copy_id(host)
    run_m.assert_called_with([copy_id_cmd, host])

    ssh.copy_id(host, user)
    run_m.assert_called_with([copy_id_cmd, str(user) + '@' + str(host)])

    ssh.copy_id(host, force=True)
    run_m.assert_called_with([copy_id_cmd, '-f', str(host)])

    ssh.copy_id(host, priv_key_path=priv_key_path)
    run_m.assert_called_with([copy_id_cmd, '-i', str(priv_key_path), str(host)])

    ssh.copy_id(host, port=port)
    run_m.assert_called_with([copy_id_cmd, '-p', str(port), str(host)])

    ssh.copy_id(host, ssh_options=ssh_options)
    ssh_options_lst = []
    for opt in ssh_options:
        ssh_options_lst.extend(['-o', opt])
    run_m.assert_called_with([copy_id_cmd] + ssh_options_lst + [host])


# def test_copy_id_output_check(mocker):
#     host = 'some-host'
#     ret_val = 'some-return-value'
#
#     mocker.patch.object(utils, 'run_subprocess_cmd', autospec=True, return_value=ret_val)
#
#     assert ssh.copy_id(host) == ret_val
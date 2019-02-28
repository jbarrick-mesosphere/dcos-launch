import json
import pytest

from unittest.mock import patch

import dcos_launch
from dcos_launch.config import get_validated_config_from_path
from dcos_launch.util import get_temp_config_path


@pytest.mark.parametrize("path", [
    'aws-onprem-with-helper.yaml',
    'aws-onprem-with-extra-iam.yaml',
    'aws-onprem-with-extra-volumes.yaml',
    'aws-onprem-coreos-prereqs.yaml',
    'aws-onprem-enterprise-with-helper.yaml',
    #'aws-onprem-with-genconf.yaml',
])
def test_generate_terraform(tmpdir, path):
    tmp_config = get_temp_config_path(tmpdir, path)
    config = get_validated_config_from_path(tmp_config)
    launcher = dcos_launch.get_launcher(config)

    with patch('subprocess.check_output', return_value=b"ssh-rsa abcdef\nssh-rsa defgeh"):
        tf = json.loads(launcher.generate_terraform())

    mod = tf['module']['dcos']

    assert tf['provider']['aws']['region'] == config['aws_region']
    assert tf['output']['masters-ips']['value'] == '${module.dcos.masters-ips}'
    assert tf['output']['cluster-address']['value'] == '${module.dcos.masters-loadbalancer}'
    assert tf['output']['public-agents-loadbalancer']['value'] == '${module.dcos.public-agents-loadbalancer}'

    assert mod['source'] == 'dcos-terraform/dcos/aws'
    assert mod['version'] == '~> 0.1'

    assert mod['cluster_name'] == config['deployment_name']
    assert mod['admin_ips'] == [config['admin_location']]

    assert mod['ssh_public_key'] == 'ssh-rsa abcdef'
    assert mod['ssh_public_key_file'] == ''

    assert mod['num_masters'] == config['num_masters']
    assert mod['num_private_agents'] == config['num_private_agents']
    assert mod['num_public_agents'] == config['num_public_agents']

    #assert mod['bootstrap_aws_ami'] == config['bootstrap_instance_ami']
    #assert mod['aws_ami'] == config['instance_ami']

    assert mod['bootstrap_instance_type'] == config['bootstrap_instance_type']
    assert mod['masters_instance_type'] == config['instance_type']
    assert mod['private_agents_instance_type'] == config['instance_type']
    assert mod['public_agents_instance_type'] == config['instance_type']

    assert mod['dcos_master_discovery'] == config['dcos_config']['master_discovery']
    assert mod['dcos_resolvers'] == '# YAML\n{}'.format(json.dumps(config['dcos_config']['resolvers']))

    if 'exhibitor_storage_backend' in config['dcos_config']:
        assert mod['dcos_exhibitor_storage_backend'] == config['dcos_config']['exhibitor_storage_backend']
    else:
        assert 'dcos_exhibitor_storage_backend' not in mod

    if 'dns_search' in config['dcos_config']:
        assert mod['dcos_dns_search'] == config['dcos_config']['dns_search']
    else:
        assert 'dcos_dns_search' not in mod

    assert mod['providers']['aws'] == 'aws'

    assert mod['custom_dcos_download_path'] == config['installer_url']
    assert mod['dcos_install_mode'] == 'install'

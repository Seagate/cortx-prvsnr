/**
* Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as published
* by the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Affero General Public License for more details.
* You should have received a copy of the GNU Affero General Public License
* along with this program. If not, see <https://www.gnu.org/licenses/>.
* For any questions about this software or licensing,
* please email opensource@seagate.com or cortx-questions@seagate.com.
*/

def remote_host() {
    hosts = "${NODE_HOST_LIST}"
    remotes = []
    hosts = hosts.split("\n")
    for (int num = 0; num < hosts.size(); num++) {
        remote_node = [:]
        remote_node.name = "node-" + num
        remote_node.host = hosts[num].split(",")[0].split("=")[1]
        remote_node.user = hosts[num].split(",")[1].split("=")[1]
        remote_node.password = hosts[num].split(",")[2].split("=")[1]
        remote_node.allowAnyHosts = true
        remotes[num] = remote_node
    }
    return remotes
}

pipeline {
    agent {
        node {
            label 'prvsnr_sanity_g4-rhev4-0658'
        }
    }

    options {
        timeout(time: 240, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '20', numToKeepStr: '20'))
    }

    environment {
        WORK_SPACE = "/root/cortx-k8s/k8_cortx_cloud"
    }

    parameters {
        string(name: 'CORTX_SCRIPTS_REPO', defaultValue: 'https://github.com/Seagate/cortx-k8s', description: 'Repository for cortx-k8s scripts (Services Team)', trim: true)
        string(name: 'CORTX_SCRIPTS_BRANCH', defaultValue: 'cortx-test', description: 'cortx-k8s scripts (Provisioner Team)', trim: true)
        text(defaultValue: '''hostname=<hostname>,user=<user>,pass=<password>''', description: 'VM details to be used. First node will be used as Master', name: 'NODE_HOST_LIST')
        booleanParam(name: 'SETUP_K8s_CLUSTER', defaultValue: false, description: 'Selecting this option will setup K8s Cluster before running Deployment.')
    }

    stages {

        stage('Setup K8s Cluster') {
            when { expression { params.SETUP_K8s_CLUSTER } }
            steps {
                script {
                    catchError(stageResult: 'FAILURE') {
                        build job: '/Cortx-kubernetes/setup-kubernetes-cluster', wait: true,
                        parameters: [
                            string(name: 'hosts', value: "${NODE_HOST_LIST}"),
                            booleanParam(name: 'PODS_ON_PRIMARY', value: "${SETUP_K8s_CLUSTER}")
                        ]
                    }
                }
            }
        }

        stage('Checkout CORTX Script') {
            steps {
                script {
                    remotes = remote_host()
                    for (remote in remotes) {
                        sshCommand remote: remote, command: """
                            cd /root
                            rm -rf cortx-k8s
                            git clone ${CORTX_SCRIPTS_REPO} -b ${CORTX_SCRIPTS_BRANCH}
                        """
                    }
                }
            }
        }

        stage('Remove solution.yaml') {
            steps {
                script {
                    for (remote in remotes) {
                        sshCommand remote: remote, command: """
                            rm -rf ${WORK_SPACE}/solution.yaml
                        """
                    }
                }
            }
        }

        stage('Update solution.yaml') {
            steps {
                sh label: "Update solution.yaml", script: '''
                    pushd ${WORKSPACE}/devops/ci
                        echo $NODE_HOST_LIST | tr ' ' '\n' > hosts
                        cat hosts
                        export WORKSPACE=${WORKSPACE}
                        export CONTROL_IMAGE=${CONTROL_IMAGE}
                        export DATA_IMAGE=${DATA_IMAGE}
                        export HA_IMAGE=${HA_IMAGE}
                        export SERVER_IMAGE=${SERVER_IMAGE}
                        sh update_solution.sh
                    popd
                '''
            }
        }

        stage('Run prerequisite script') {
            steps {
                script {
                    for (remote in remotes) {
                        sshCommand remote: remote, command: """
                            cd ${WORK_SPACE}
                            ./prereq-deploy-cortx-cloud.sh -d /dev/sdb
                        """
                    }
                }
            }
        }

        stage('Deploy CORTX Cluster') {
            steps {
                script {
                    sshCommand remote: remotes[0], command: """
                        cd ${WORK_SPACE}
                        sh deploy-cortx-cloud.sh
                    """
                }
            }
        }
    }

    post {

        success {
            script {
                sshCommand remote: remotes[0], command: """
                    kubectl get pods
                """
            }
        }

        always {
            script {
                def recipientProvidersClass = [[$class: 'RequesterRecipientProvider']]
                emailext (
                    body: '''${SCRIPT, template="cluster-setup-email.template"}''',
                    mimeType: 'text/html',
                    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                    attachLog: true,
                    recipientProviders: recipientProvidersClass
                )
            }
        }
    }
}

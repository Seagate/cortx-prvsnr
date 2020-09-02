pipeline { 
    agent {
        node {
            label 'docker-prvsnr-node'
        }
    }
    
    options {
        timeout(time: 15, unit: 'MINUTES') 
    }
    
    stages {
        stage('Prepare') {
            steps {
                deleteDir()

                sh encoding: 'utf-8', label: 'Install Python', returnStdout: true, script: 'yum install -y python'
                sh encoding: 'utf-8', label: 'Cleanup', returnStdout: true, script: 'test -d /root/rpmbuild && rm -rf /root/rpmbuild || echo "/root/rpmbuild absent. Skipping cleanup..."'
            }
        }
        stage('Checkout') {
            steps {
                 git branch: 'master', credentialsId: '1f8776fd-39de-4356-ba0a-a40895719a3d', url: 'https://github.com/Seagate/cortx-prvsnr.git'
            }
        }
        stage('Package: Provisioner RPMS') {
            steps {
                sh encoding: 'utf-8', label: 'Provisioner RPMS', returnStdout: true, script: """
                    sh ./devops/rpms/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 1.0.0 -b ${BUILD_NUMBER}
                """
            }
        }
        stage('Package: Provisioner CLI RPMS') {
            steps {
                sh encoding: 'utf-8', label: 'Provisioner CLI RPMS', returnStdout: true, script: """
                    sh ./cli/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 1.0.0 -b ${BUILD_NUMBER}
                """
            }
        }
        stage('Upload') {
            steps {
                sh encoding: 'utf-8', label: '', returnStdout: true, script: '''
                    rm -rf /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER}
                    test -d /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER} || mkdir -p /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER}
                    cp /root/rpmbuild/RPMS/x86_64/cortx-prvsnr* /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER}
                '''
            }
        }
        stage('Create Repo') {
            steps {
                sh encoding: 'utf-8', label: 'install_prereqs', returnStdout: true, script: '''
                    rpm --quiet -qi createrepo || yum install -q -y createrepo && echo "createrepo already installed."
                    pushd /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER}
                    createrepo .
                    popd
                '''
            }
        }
        stage('Release') {
            steps {
                sh encoding: 'utf-8', label: '', returnStdout: true, script: '''
                    test -d /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful && rm -rf /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful
                    test -d /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful || mkdir /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful
                    pushd /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful
                    ln -s /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/${BUILD_NUMBER} repo
                    popd
                '''
            }
        }
        stage('Link: Last Successful'){
            steps {
                sh encoding: 'utf-8', label: 'last_successful', returnStdout: true, script: """
                    pushd /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/
                    test -d /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/last_successful && rm -f last_successful
                    ln -s /mnt/bigstorage/releases/cortx/components/github/dev/rhel-7.7.1908/dev/provisioner/$BUILD_NUMBER last_successful
                    popd
                """
            }
        }
    }
	
	post {
        success {
            emailext (
			subject: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
			body: """
			<h><span style=color:green>SUCCESSFUL:</span> Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</h>
			<p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>
			<p>RPM's are located at http://cortx-storage.colo.seagate.com/releases/eos/components/dev/provisioner/${env.BUILD_NUMBER}</p>
			""",
			recipientProviders: [[$class: 'DevelopersRecipientProvider']]
			)
			
        }
		
		failure {
            emailext (
			subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
			body: """
			<h><span style=color:red>FAILED:</span> Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</h>
			<p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>
			""",
			to: 'shailesh.vaidya@seagate.com',
			recipientProviders: [[$class: 'DevelopersRecipientProvider'],[$class: 'RequesterRecipientProvider']]
			)
			
        }
		
    }
}

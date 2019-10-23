pipeline { 
    agent {
        node {
            label 'centos7.5_1804'
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
                git branch: 'master', credentialsId: 'ees-prvsnr_ssh', url: 'ssh://git@gitlab.mero.colo.seagate.com:6022/eos/provisioner/ees-prvsnr.git'
            }
        }
        stage('Package: Provisioner RPMS') {
            steps {
                sh encoding: 'utf-8', label: 'Provisioner RPMS', returnStdout: true, script: """
                    sh ./rpms/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 1.0.0 -b ${BUILD_NUMBER}
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
                    cp /root/rpmbuild/RPMS/x86_64/eos-prvsnr* /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER}
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
                    test -d /mnt/bigstorage/releases/master/last_successful/provisioner && rm -rf /mnt/bigstorage/releases/master/last_successful/provisioner
                    test -d /mnt/bigstorage/releases/master/last_successful/provisioner || mkdir /mnt/bigstorage/releases/master/last_successful/provisioner
                    pushd /mnt/bigstorage/releases/master/last_successful/provisioner
                    ln -s /mnt/bigstorage/releases/eos/components/dev/provisioner/${BUILD_NUMBER} repo
                    popd
                '''
            }
        }
        stage('Link: Last Successful'){
            steps {
                sh encoding: 'utf-8', label: 'last_successful', returnStdout: true, script: """
                    pushd /mnt/bigstorage/releases/eos/components/dev/provisioner/
                    test -d /mnt/bigstorage/releases/eos/components/dev/provisioner/last_successful && rm -f last_successful
                    ln -s /mnt/bigstorage/releases/eos/components/dev/provisioner/$BUILD_NUMBER last_successful
                    popd
                """
            }
        }
    }
}

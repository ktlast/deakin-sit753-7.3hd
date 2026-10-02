pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '3'))
    }
    stages {
        stage('Build') {
            steps { dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/build.sh\"" } }
        }
        stage('Test') {
            steps { dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/test.sh\"" } }
            post {
                always {
                    dir("${env.RUNTIME_DIR}/workspace") { junit testResults: 'results/tests/junit.xml', allowEmptyResults: true }
                }
            }
        }
        stage('Code Quality') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/quality.sh\"" }
                }
            }
        }
        stage('Security') {
            steps { dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/security.sh\"" } }
        }
        stage('Deploy') {
            steps { dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/deploy.sh\"" } }
        }
        stage('Release') {
            steps { dir("${env.RUNTIME_DIR}/workspace") { sh "bash \"${env.PROJECT_DIR}/scripts/release.sh\"" } }
        }
    }
    post {
        always {
            dir("${env.RUNTIME_DIR}/workspace") { archiveArtifacts artifacts: 'results/**/*', allowEmptyArchive: true }
        }
    }
}

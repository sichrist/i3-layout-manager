#!groovy
pipeline {
    agent any

    stages {
        stage('SonarQube analyzing...'){
            steps{
                sh '/opt/sonar-scanner/bin/sonar-scanner'
            }
        }
	}
}
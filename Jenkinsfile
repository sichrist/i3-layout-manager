#!groovy
pipeline {
    agent any

    stages {
    	stage('SonarQube analyzing...'){
		sh '/opt/sonar-scanner/bin/sonar-scanner'
        }
	}
}
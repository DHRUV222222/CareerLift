pipeline {
    agent {
        kubernetes {
            yamlFile 'podTemplate.yaml'
        }
    }

    environment {
        NEXUS_REGISTRY = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'
        LOCAL_REGISTRY = '127.0.0.1:30085'
        IMAGE_NAME = "careerlift-app"
        DOCKER_IMAGE = "${LOCAL_REGISTRY}/careerlift/${IMAGE_NAME}:${BUILD_NUMBER}"

        SONAR_ANALYSIS = "true"
        SONAR_HOST = 'http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000'
        SONAR_PROJECT_KEY = '2401185_CareerLift'
        SONAR_PROJECT_NAME = 'CareerLift'
        SONAR_TOKEN = 'sqp_e70dca117aaa445364015a3235a50530a178ae09'

        KUBE_NAMESPACE = "careerlift-ns"
    }

    stages {

        stage('Checkout Code') {
            steps {
                container('sonar-scanner') {
                    checkout scm
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    sh """
                        echo "Building Docker image..."
                        docker build -t ${IMAGE_NAME}:latest .
                        docker tag ${IMAGE_NAME}:latest ${DOCKER_IMAGE}
                    """
                }
            }
        }

        stage('Push to Local Minikube Registry') {
            steps {
                container('dind') {
                    sh """
                        echo "Pushing image to local registry..."
                        docker push ${DOCKER_IMAGE}
                    """
                }
            }
        }

        stage('SonarQube Analysis') {
            when { environment name: 'SONAR_ANALYSIS', value: 'true' }
            steps {
                container('sonar-scanner') {
                    sh """
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.projectName=${SONAR_PROJECT_NAME} \
                            -Dsonar.host.url=${SONAR_HOST} \
                            -Dsonar.token=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}
                        kubectl set image deployment/careerlift careerlift=${DOCKER_IMAGE} -n ${KUBE_NAMESPACE}
                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE}
                    """
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed"
        }
    }
}

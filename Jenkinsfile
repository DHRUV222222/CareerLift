pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:

  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command: ["tail", "-f", "/dev/null"]
    tty: true

  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["tail", "-f", "/dev/null"]
    tty: true
    securityContext:
      runAsUser: 0
    env:
    - name: KUBECONFIG
      value: /kube/config
    volumeMounts:
    - name: kubeconfig-secret
      mountPath: /kube/config
      subPath: kubeconfig

  - name: dind
    image: docker:dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-config
      mountPath: /etc/docker/daemon.json
      subPath: daemon.json

  volumes:
  - name: docker-config
    configMap:
      name: docker-daemon-config

  - name: kubeconfig-secret
    secret:
      secretName: kubeconfig-secret
'''
        }
    }

    environment {
        NEXUS_INTERNAL = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"
        NEXUS_NODEPORT = "127.0.0.1:30085"
        IMAGE_NAME = "careerlift/careerlift-app"
        DOCKER_IMAGE_INTERNAL = "${NEXUS_INTERNAL}/${IMAGE_NAME}:${BUILD_NUMBER}"
        DOCKER_IMAGE_NODEPORT = "${NEXUS_NODEPORT}/${IMAGE_NAME}:${BUILD_NUMBER}"
        KUBE_NAMESPACE = "careerlift-ns"

        SONAR_HOST = "http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000"
        SONAR_PROJECT_KEY = "2401185_CareerLift"
        SONAR_PROJECT_NAME = "CareerLift"
        SONAR_TOKEN = "sqp_e70dca117aaa445364015a3235a50530a178ae09"
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
                    sh '''
                        echo "Building Docker image..."
                        sleep 5
                        docker build -t careerlift-app:latest .
                        docker image ls
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                container('dind') {
                    sh '''
                        docker run --rm careerlift-app:latest pytest || true
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar-scanner') {
                    sh """
                        sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.projectName=${SONAR_PROJECT_NAME} \
                          -Dsonar.host.url=${SONAR_HOST} \
                          -Dsonar.token=${SONAR_TOKEN} \
                          -Dsonar.sources=.
                    """
                }
            }
        }

        stage('Push Image to Nexus') {
            steps {
                container('dind') {
                    sh """
                        echo "Logging in to Nexus..."
                        echo "Changeme@2025" | docker login ${NEXUS_INTERNAL} -u admin --password-stdin

                        docker tag careerlift-app:latest ${DOCKER_IMAGE_INTERNAL}
                        docker push ${DOCKER_IMAGE_INTERNAL}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}
                        kubectl set image deployment/careerlift careerlift=${DOCKER_IMAGE_INTERNAL} -n ${KUBE_NAMESPACE}
                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=600s
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

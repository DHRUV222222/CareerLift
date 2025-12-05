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
    command: ["cat"]
    tty: true

  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["cat"]
    tty: true
    securityContext:
      runAsUser: 0
      readOnlyRootFilesystem: false
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
        NEXUS_REGISTRY = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'
        DOCKER_IMAGE = "${NEXUS_REGISTRY}/careerlift/careerlift-app:${BUILD_NUMBER}"

        // Kubernetes uses NodePort registry instead
        K8S_IMAGE = "127.0.0.1:30085/careerlift/careerlift-app:${BUILD_NUMBER}"

        KUBE_NAMESPACE = 'careerlift-ns'

        // SonarQube
        SONAR_HOST = 'http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000'
        SONAR_PROJECT_KEY = '2401185_CareerLift'
        SONAR_PROJECT_NAME = 'CareerLift'
        SONAR_TOKEN = 'sqp_e70dca117aaa445364015a3235a50530a178ae09'
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
                        sleep 10
                        docker build -t careerlift-app:latest .
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
                          -Dsonar.projectName=\"${SONAR_PROJECT_NAME}\" \
                          -Dsonar.host.url=${SONAR_HOST} \
                          -Dsonar.token=${SONAR_TOKEN} \
                          -Dsonar.sources=. \
                          -Dsonar.python.coverage.reportPaths=coverage.xml \
                          -Dsonar.python.version=3.10
                    """
                }
            }
        }

        stage('Login to Nexus Registry') {
            steps {
                container('dind') {
                    sh """
                        echo "Changeme@2025" | docker login ${NEXUS_REGISTRY} -u admin --password-stdin
                    """
                }
            }
        }

        stage('Push Image to Nexus') {
            steps {
                container('dind') {
                    sh """
                        docker tag careerlift-app:latest ${DOCKER_IMAGE}
                        docker push ${DOCKER_IMAGE}

                        # Push also to 127.0.0.1:30085 for Kubernetes
                        docker tag careerlift-app:latest ${K8S_IMAGE}
                        docker push ${K8S_IMAGE}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}

                        kubectl set image deployment/careerlift \
                            careerlift=${K8S_IMAGE} -n ${KUBE_NAMESPACE}

                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=600s
                    """
                }
            }
        }
    }
}

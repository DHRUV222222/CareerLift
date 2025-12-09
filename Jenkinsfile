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
    volumeMounts:
    - mountPath: /home/jenkins/agent
      name: workspace-volume

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
    - mountPath: /home/jenkins/agent
      name: workspace-volume

  - name: dind
    image: docker:20.10-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-lib
      mountPath: /var/lib/docker
    - mountPath: /home/jenkins/agent
      name: workspace-volume

  volumes:
  - name: docker-lib
    emptyDir: {}
  - name: workspace-volume
    emptyDir: {}
  - name: kubeconfig-secret
    secret:
      secretName: kubeconfig-secret
'''
        }
    }

    environment {
        INTERNAL_REGISTRY = "127.0.0.1:30085"
        NEXUS_REGISTRY = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"

        IMAGE_NAME = "careerlift-app"
        IMAGE_TAG = "${BUILD_NUMBER}"

        PUSH_IMAGE = "${INTERNAL_REGISTRY}/careerlift/${IMAGE_NAME}:${IMAGE_TAG}"

        KUBE_NAMESPACE = "careerlift-ns"

        SONAR_HOST = "http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000"
        SONAR_PROJECT_KEY = "2401185_CareerLift"
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
                            -Dsonar.host.url=${SONAR_HOST} \
                            -Dsonar.token=${SONAR_TOKEN} \
                            -Dsonar.sources=. \
                            -Dsonar.python.version=3.10
                    """
                }
            }
        }

        stage('Push Image') {
            steps {
                container('dind') {
                    sh '''
                        echo "Tagging image..."
                        docker tag careerlift-app:latest ''' + "${PUSH_IMAGE}" + '''

                        echo "Pushing image to internal registry..."
                        docker push ''' + "${PUSH_IMAGE}" + '''
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}

                        kubectl set image deployment/careerlift \
                          careerlift=${PUSH_IMAGE} -n ${KUBE_NAMESPACE}

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

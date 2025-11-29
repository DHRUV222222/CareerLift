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
        NEXUS_URL = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"
        IMAGE_NAME = "careerlift-app"
        DOCKER_IMAGE = "${NEXUS_URL}/careerlift/${IMAGE_NAME}:${BUILD_NUMBER}"
        KUBE_NAMESPACE = "careerlift-ns"
        SONAR_TOKEN = "sqp_64723a56f6198e4a7501fd240f37720c24c8a166"
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
                        docker image ls
                    '''
                }
            }
        }

        stage('Run Tests in Docker') {
            steps {
                container('dind') {
                    sh '''
                        docker run --rm careerlift-app:latest \
                        pytest --maxfail=1 --disable-warnings --ds=careerlift.settings \
                        --junitxml=reports/junit.xml \
                        --cov=. --cov-report=xml:coverage.xml
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar-scanner') {
                    sh """
                        sonar-scanner \
                            -Dsonar.projectKey=2401185 \
                            -Dsonar.projectName=careerlift \
                            -Dsonar.host.url=http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000 \
                            -Dsonar.login=${SONAR_TOKEN} \
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
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'nexus-credentials',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASSWORD'
                        )
                    ]) {
                        sh '''
                            docker login ${NEXUS_URL} -u $NEXUS_USER -p $NEXUS_PASSWORD
                        '''
                    }
                }
            }
        }

        stage('Tag & Push Image to Nexus') {
            steps {
                container('dind') {
                    sh '''
                        docker tag careerlift-app:latest ${DOCKER_IMAGE}
                        docker push ${DOCKER_IMAGE}
                        docker image ls
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        kubectl get namespace ${KUBE_NAMESPACE} || kubectl create namespace ${KUBE_NAMESPACE}

                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}

                        kubectl set image deployment/careerlift \
                            careerlift=${DOCKER_IMAGE} -n ${KUBE_NAMESPACE}

                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=300s
                    """
                }
            }
        }
    }

    post {
        always {
            container('dind') {
                sh 'docker system prune -f'
            }
            cleanWs()
        }
        success {
            echo "✅ Pipeline Completed Successfully!"
        }
        failure {
            echo "❌ Pipeline Failed!"
        }
    }
}

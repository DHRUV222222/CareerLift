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
        KUBE_NAMESPACE = 'careerlift-ns'
        SONAR_TOKEN = credentials('sonar-token')
        IMAGE_TAG = "${BUILD_NUMBER}"
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
                        --cov=. --cov-report=xml:coverage.xml || true
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                SONAR_HOST = 'http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000'
                SONAR_PROJECT_KEY = '2401185_CareerLift'
                SONAR_PROJECT_NAME = 'CareerLift'
            }
            steps {
                container('sonar-scanner') {
                    script {
                        try {
                            echo "🔍 Starting SonarQube analysis..."
                            echo "Project: ${SONAR_PROJECT_KEY}"
                            echo "Host: ${SONAR_HOST}"
                            
                            sh """
                                sonar-scanner \
                                    -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                    -Dsonar.projectName="${SONAR_PROJECT_NAME}" \
                                    -Dsonar.host.url=${SONAR_HOST} \
                                    -Dsonar.token=${SONAR_TOKEN} \
                                    -Dsonar.sources=. \
                                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                                    -Dsonar.python.version=3.10 \
                                    -Dsonar.sourceEncoding=UTF-8 \
                                    -Dsonar.scm.disabled=true
                            """
                            
                            echo "✅ SonarQube analysis completed successfully"
                        } catch (err) {
                            error "❌ SonarQube analysis failed: ${err.message}"
                        }
                    }
                }
            }
        }

        stage('Login to Nexus Registry') {
            environment {
                NEXUS_REGISTRY = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'
                NEXUS_USER = 'admin'
                NEXUS_PASSWORD = 'Changeme@2025'
            }
            steps {
                container('dind') {
                    script {
                        try {
                            echo "🔑 Attempting to log in to Nexus registry..."
                            sh """
                                if ! echo "$NEXUS_PASSWORD" | docker login ${NEXUS_REGISTRY} -u $NEXUS_USER --password-stdin; then
                                    echo "❌ Failed to log in to Nexus registry"
                                    exit 1
                                fi
                                echo "✅ Successfully logged in to Nexus registry"
                            """
                        } catch (err) {
                            error "❌ Nexus registry login failed: ${err.message}"
                        }
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
                // Clean up workspace
                sh 'rm -rf * .* || true'
            }
            // Clean workspace using deleteDir instead of cleanWs
            deleteDir()
        }
        success {
            echo "✅ Pipeline Completed Successfully!"
        }
        failure {
            echo "❌ Pipeline Failed! Check the logs above for details."
        }
        cleanup {
            // Clean up any remaining resources
            echo 'Cleaning up workspace...'
        }
    }
}

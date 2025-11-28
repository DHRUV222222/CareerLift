pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.10-slim
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: ssh-credentials
      mountPath: /root/.ssh
      readOnly: true

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
  - name: ssh-credentials
    secret:
      secretName: ssh-credentials
      defaultMode: 0600
'''
        }
    }

    environment {
        NEXUS_URL = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'
        DOCKER_IMAGE = "${NEXUS_URL}/careerlift/careerlift-app:${env.BUILD_NUMBER}"
        KUBE_NAMESPACE = 'careerlift-ns'
    }
    
    stages {

        stage('Checkout') {
            steps {
                container('python') {
                    checkout scm
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                container('python') {
                    sh '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install coverage pytest pytest-cov
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                container('python') {
                    sh '''
                    coverage run --source='.' manage.py test
                    coverage report -m
                    coverage xml
                    '''
                    junit '**/test-reports/*.xml'
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
                        -Dsonar.login=sqp_64723a56f6198e4a7501fd240f37720c24c8a166 \
                        -Dsonar.sources=. \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.python.version=3.10
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    script {
                        docker.build("${DOCKER_IMAGE}")
                    }
                }
            }
        }

        stage('Login to Nexus') {
            steps {
                container('dind') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'nexus-credentials',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASSWORD'
                        )
                    ]) {
                        sh """
                        docker login ${NEXUS_URL} -u $NEXUS_USER -p $NEXUS_PASSWORD
                        """
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                container('dind') {
                    sh """
                    docker push ${DOCKER_IMAGE}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    withCredentials([
                        string(credentialsId: 'django-secret-key', variable: 'DJANGO_SECRET_KEY'),
                        usernamePassword(credentialsId: 'db-credentials', 
                                       usernameVariable: 'DB_USER', 
                                       passwordVariable: 'DB_PASSWORD')
                    ]) {
                        sh """
                        kubectl get namespace ${KUBE_NAMESPACE} || kubectl create namespace ${KUBE_NAMESPACE}
                        
                        if ! kubectl get secret careerlift-secrets -n ${KUBE_NAMESPACE}; then
                            kubectl create secret generic careerlift-secrets \
                                --from-literal=DJANGO_SECRET_KEY='${DJANGO_SECRET_KEY}' \
                                --from-literal=DB_USER='${DB_USER}' \
                                --from-literal=DB_PASSWORD='${DB_PASSWORD}' \
                                -n ${KUBE_NAMESPACE}
                        fi

                        kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}

                        kubectl set image deployment/careerlift careerlift=${DOCKER_IMAGE} -n ${KUBE_NAMESPACE} || true

                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=300s

                        echo "✅ Deployment successful!"
                        """
                    }
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
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}

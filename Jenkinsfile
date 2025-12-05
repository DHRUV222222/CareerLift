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
    tty: true
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
        // registry accessible from inside k8s cluster (used by deployment)
        NEXUS_REGISTRY = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'

        // repository and tag used when pushing
        IMAGE_REPO = "${NEXUS_REGISTRY}/careerlift/careerlift-app"

        // final image pushed by pipeline
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKER_IMAGE = "${IMAGE_REPO}:${IMAGE_TAG}"

        KUBE_NAMESPACE = 'careerlift-ns'

        // Toggle sonar analysis: 'true' or 'false'
        SONAR_ANALYSIS = 'true'
        SONAR_HOST = 'http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000'
        SONAR_PROJECT_KEY = '2401185_CareerLift'
        SONAR_PROJECT_NAME = 'CareerLift'
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
                        sleep 5
                        echo "Building docker image: careerlift-app:latest"
                        docker build -t careerlift-app:latest .
                        docker image ls | head -n 20
                    '''
                }
            }
        }

        stage('Run Tests in Docker') {
            steps {
                container('dind') {
                    sh '''
                        echo "Running tests (non-blocking)..."
                        docker run --rm careerlift-app:latest \
                          pytest --maxfail=1 --disable-warnings --ds=careerlift.settings \
                          --junitxml=reports/junit.xml \
                          --cov=. --cov-report=xml:coverage.xml || true
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                environment name: 'SONAR_ANALYSIS', value: 'true'
            }
            steps {
                container('sonar-scanner') {
                    script {
                        // SONAR_TOKEN should be set up as Jenkins credential (type: Secret text) id: sonar-token
                        withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                            sh """
                                echo "Running sonar-scanner..."
                                sonar-scanner \
                                  -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                  -Dsonar.projectName=${SONAR_PROJECT_NAME} \
                                  -Dsonar.host.url=${SONAR_HOST} \
                                  -Dsonar.token=${SONAR_TOKEN} \
                                  -Dsonar.sources=. \
                                  -Dsonar.python.coverage.reportPaths=coverage.xml \
                                  -Dsonar.python.version=3.10 \
                                  -Dsonar.sourceEncoding=UTF-8
                            """
                        }
                    }
                }
            }
        }

        stage('Login to Nexus Registry') {
            steps {
                container('dind') {
                    script {
                        // Ensure you have created Jenkins credentials (usernamePassword) with id: nexus-credentials
                        withCredentials([usernamePassword(credentialsId: 'nexus-credentials', usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
                            sh '''
                                echo "Logging in to Nexus registry: ${NEXUS_REGISTRY}"
                                echo "$NEXUS_PASS" | docker login ${NEXUS_REGISTRY} -u "$NEXUS_USER" --password-stdin
                                docker info | head -n 20
                            '''
                        }
                    }
                }
            }
        }

        stage('Tag & Push Image to Nexus') {
            steps {
                container('dind') {
                    sh '''
                        echo "Tagging and pushing image ${DOCKER_IMAGE}"
                        docker tag careerlift-app:latest ${DOCKER_IMAGE}
                        docker push ${DOCKER_IMAGE}
                        docker image ls | head -n 20
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    script {
                        echo "Applying k8s manifests and updating deployment image..."

                        // Create namespace if missing
                        sh """
                            if ! kubectl get namespace ${KUBE_NAMESPACE} >/dev/null 2>&1; then
                                kubectl create namespace ${KUBE_NAMESPACE}
                            fi
                        """

                        // Apply manifests (make sure k8s_deployment.yaml is in repo and uses the same image repository)
                        sh "kubectl apply -f k8s_deployment.yaml -n ${KUBE_NAMESPACE}"

                        // Update deployment image to the pushed tag
                        sh """
                            kubectl set image deployment/careerlift careerlift=${DOCKER_IMAGE} -n ${KUBE_NAMESPACE} --record
                        """

                        // Wait for rollout (increase timeout if your app starts slow)
                        def rc = sh(script: "kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=600s", returnStatus: true)
                        if (rc != 0) {
                            echo "Rollout failed or timed out. Gathering diagnostics..."
                            sh """
                                kubectl describe deployment/careerlift -n ${KUBE_NAMESPACE} || true
                                kubectl get pods -n ${KUBE_NAMESPACE} -o wide || true
                                kubectl logs -l app=careerlift -n ${KUBE_NAMESPACE} --tail=100 || true
                            """
                            error("Deployment rollout failed. See logs above.")
                        } else {
                            echo "✅ Deployment rolled out successfully."
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            container('dind') {
                sh 'docker system prune -f || true'
            }
            // Cleanup workspace on agent
            deleteDir()
        }
        success {
            echo "✅ Pipeline completed."
        }
        failure {
            echo "❌ Pipeline failed. Check the console logs."
        }
    }
}

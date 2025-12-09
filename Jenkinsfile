pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:

  # Sonar Scanner
  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  # Kubectl
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["cat"]
    tty: true
    env:
    - name: KUBECONFIG
      value: /kube/config
    securityContext:
      runAsUser: 0
      readOnlyRootFilesystem: false
    volumeMounts:
    - name: kubeconfig-secret
      mountPath: /kube/config
      subPath: kubeconfig
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  # Docker-in-Docker FIXED
  - name: dind
    image: docker:dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    - name: DOCKER_HOST
      value: "tcp://127.0.0.1:2375"
    ports:
    - containerPort: 2375
    volumeMounts:
    - name: docker-lib
      mountPath: /var/lib/docker
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  # Jenkins agent
  - name: jnlp
    image: jenkins/inbound-agent:latest
    args: ["$(JENKINS_SECRET)", "$(JENKINS_NAME)"]
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

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
        # Registry inside cluster
        NEXUS_INTERNAL = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"

        # Internal Nexus for Jenkins build
        DOCKER_IMAGE = "${NEXUS_INTERNAL}/careerlift/careerlift-app:${BUILD_NUMBER}"

        # Sonar
        SONAR_HOST = "http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000"
        SONAR_PROJECT_KEY = "2401185_CareerLift"
        SONAR_PROJECT_NAME = "CareerLift"
        SONAR_TOKEN = "sqp_e70dca117aaa445364015a3235a50530a178ae09"

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
                    sh '''
                        echo "Waiting for Dockerd to start..."
                        sleep 10
                        
                        docker info || (echo "Docker not running!" && exit 1)

                        echo "Building Docker image..."
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
                          -Dsonar.projectName=${SONAR_PROJECT_NAME} \
                          -Dsonar.host.url=${SONAR_HOST} \
                          -Dsonar.token=${SONAR_TOKEN} \
                          -Dsonar.sources=. \
                          -Dsonar.python.coverage.reportPaths=coverage.xml
                    """
                }
            }
        }

        stage('Push Image to Nexus') {
            steps {
                container('dind') {
                    sh """
                        echo "Logging in..."
                        echo "Changeme@2025" | docker login ${NEXUS_INTERNAL} -u admin --password-stdin

                        docker tag careerlift-app:latest ${DOCKER_IMAGE}
                        docker push ${DOCKER_IMAGE}
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
                        kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=600s
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed — check logs"
        }
    }
}

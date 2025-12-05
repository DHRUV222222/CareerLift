pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command: ['cat']
    tty: true

  - name: kubectl
    image: bitnami/kubectl:latest
    command: ['cat']
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
    image: docker:24-dind
    securityContext:
      privileged: true
    env:
      - name: DOCKER_TLS_CERTDIR
        value: ""
    # make dockerd listen on tcp so other container in same pod can talk to it
    command:
      - "dockerd-entrypoint.sh"
      - "--host=tcp://0.0.0.0:2375"
    tty: true
    volumeMounts:
      - name: docker-config
        mountPath: /etc/docker/daemon.json
        subPath: daemon.json

  - name: docker
    image: docker:24-cli
    command: ['cat']
    tty: true
    env:
      - name: DOCKER_HOST
        value: "tcp://localhost:2375"

  volumes:
    - name: docker-config
      configMap:
        name: docker-daemon-config
    - name: kubeconfig-secret
      secret:
        secretName: kubeconfig-secret
"""
    }
  }

  environment {
    NEXUS_REGISTRY = 'nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085'
    IMAGE_NAME = 'careerlift-app'
    IMAGE_TAG  = "${BUILD_NUMBER}"
    DOCKER_IMAGE = "${NEXUS_REGISTRY}/careerlift/${IMAGE_NAME}:${IMAGE_TAG}"
    KUBE_NAMESPACE = 'careerlift-ns'

    // Sonar (optional)
    SONAR_ANALYSIS = 'true'
    SONAR_HOST = 'http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000'
    SONAR_PROJECT_KEY = '2401185_CareerLift'
    SONAR_PROJECT_NAME = 'CareerLift'
    SONAR_TOKEN = credentials('sonar-token') // use Jenkins credentials plugin (string) id 'sonar-token'
  }

  stages {
    stage('Checkout') {
      steps {
        container('sonar-scanner') { checkout scm }
      }
    }

    stage('Build Docker Image') {
      steps {
        container('docker') {
          sh '''
            echo "Waiting for dockerd..."
            # simple wait loop to ensure dind's dockerd accepts connections
            n=0
            until docker info >/dev/null 2>&1; do
              sleep 1
              n=$((n+1))
              if [ $n -gt 60 ]; then
                echo "dockerd did not become available"
                docker info || true
                exit 1
              fi
            done

            echo "Building image: ${IMAGE_NAME}:latest"
            docker build -t ${IMAGE_NAME}:latest .
            docker image ls --format "{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}"
          '''
        }
      }
    }

    stage('Run Tests') {
      steps {
        container('docker') {
          sh '''
            # run tests inside container image
            docker run --rm ${IMAGE_NAME}:latest pytest --disable-warnings --ds=careerlift.settings --junitxml=reports/junit.xml --cov=. --cov-report=xml:coverage.xml || true
          '''
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
              -Dsonar.token=${SONAR_TOKEN} \
              -Dsonar.sources=. \
              -Dsonar.python.coverage.reportPaths=coverage.xml \
              -Dsonar.sourceEncoding=UTF-8
          """
        }
      }
    }

    stage('Login to Nexus') {
      steps {
        container('docker') {
          withCredentials([usernamePassword(credentialsId: 'nexus-credentials', usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
            sh '''
              echo "${NEXUS_PASS}" | docker login ${NEXUS_REGISTRY} -u "${NEXUS_USER}" --password-stdin
            '''
          }
        }
      }
    }

    stage('Tag & Push') {
      steps {
        container('docker') {
          sh '''
            docker tag ${IMAGE_NAME}:latest ${DOCKER_IMAGE}
            docker push ${DOCKER_IMAGE}
            docker image ls --format "{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}"
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
            kubectl set image deployment/careerlift careerlift=${DOCKER_IMAGE} -n ${KUBE_NAMESPACE} --record
            kubectl rollout status deployment/careerlift -n ${KUBE_NAMESPACE} --timeout=600s
          """
        }
      }
    }
  }

  post {
    always {
      container('docker') {
        sh 'docker system prune -f || true'
      }
      deleteDir()
    }
    success { echo "✅ Pipeline succeeded" }
    failure { echo "❌ Pipeline failed — check logs" }
  }
}

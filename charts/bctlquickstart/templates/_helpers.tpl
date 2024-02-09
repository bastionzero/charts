{{/*
Expand the name of the chart.
*/}}
{{- define "bctlquickstartchart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bctlquickstartchart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "bctlquickstartchart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "bctlquickstartchart.labels" -}}
helm.sh/chart: {{ include "bctlquickstartchart.chart" . }}
{{ include "bctlquickstartchart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "bctlquickstartchart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bctlquickstartchart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create the name of the quickstart service account to use
*/}}
{{- define "bctlquickstartchart.quickstartServiceAccountName" -}}
{{- default (print "bctl-" .Values.clusterName "-quickstart-sa")  .Values.quickstart.quickstartServiceAccount }}
{{- end }}

{{/*
Create the bctl-quickstart-job name
*/}}
{{- define "bctlquickstartchart.quickstartJobName" -}}
{{- default (print "bctl-" .Values.clusterName "-quickstart")  .Values.quickstart.quickstartJobName }}
{{- end }}

{{/*
Create the bctl-quickstart-Role name
*/}}
{{- define "bctlquickstartchart.quickstartRoleName" -}}
{{- printf "%s-role" (include "bctlquickstartchart.quickstartServiceAccountName" .) }}
{{- end }}

{{/*
Create the bctl-quickstart-RoleBinding name
*/}}
{{- define "bctlquickstartchart.quickstartRoleBindingName" -}}
{{- printf "%s-rolebinding" (include "bctlquickstartchart.quickstartServiceAccountName" .) }}
{{- end }}

{{/*
Create the name of the cleanup service account to use
*/}}
{{- define "bctlquickstartchart.cleanupServiceAccountName" -}}
{{- print "bctl-" .Values.clusterName "-cleanup-sa" }}
{{- end }}

{{/*
Create the bctl-cleanup-job name
*/}}
{{- define "bctlquickstartchart.cleanupJobName" -}}
{{- print "bctl-" .Values.clusterName "-cleanup-job" }}
{{- end }}

{{/*
Create the bctl-cleanup-Role name
*/}}
{{- define "bctlquickstartchart.cleanupRoleName" -}}
{{- printf "%s-role" (include "bctlquickstartchart.cleanupServiceAccountName" .) }}
{{- end }}

{{/*
Create the bctl-cleanup-RoleBinding name
*/}}
{{- define "bctlquickstartchart.cleanupRoleBindingName" -}}
{{- printf "%s-rolebinding" (include "bctlquickstartchart.cleanupServiceAccountName" .) }}
{{- end }}


{{/*
Create the name of the agent service account to use
*/}}
{{- define "bctlquickstartchart.agentServiceAccountName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent-sa") .Values.agent.serviceAccountName }}
{{- end }}

{{/*
Create the name of the agent secret to use
*/}}
{{- define "bctlquickstartchart.agentSecretName" -}}
{{- print "bctl-" .Values.clusterName "-secret" }}
{{- end }}

{{/*
Create the name of the agent rolebinding to use
*/}}
{{- define "bctlquickstartchart.agentRoleBindingName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent-rolebinding") .Values.agent.roleBindingName }}
{{- end }}

{{/*
Create the name of the agent role to use
*/}}
{{- define "bctlquickstartchart.agentRoleName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent-role") .Values.agent.roleName }}
{{- end }}

{{/*
Create the name of the deployment to use
*/}}
{{- define "bctlquickstartchart.agentDeploymentName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent") .Values.agent.deploymentName }}
{{- end }}

{{/*
Create the name of the agent clusterrolebinnding to use
*/}}
{{- define "bctlquickstartchart.agentClusterRoleBindingName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent-clusterrolebinding") .Values.agent.clusterName }}
{{- end }}

{{/*
Create the name of the agent clusterrole to use
*/}}
{{- define "bctlquickstartchart.agentClusterRoleName" -}}
{{- default (print "bctl-" .Values.clusterName "-agent-clusterrole") .Values.agent.clusterRoleName }}
{{- end }}

{{/* 
Ensure the user has passed an api key or a ref to a secret
*/}}
{{- define "bctlquickstartchart.apiKeyOrRef"}}
{{- if .Values.apiKey }}
{{- .Values.apiKey -}}
{{- else if .Values.apiKeyExistingSecret }}
{{- .Values.apiKeyExistingSecret -}}
{{- else }}
{{- fail "A valid .Values.apiKey or apiKeyExistingSecret entry required!" }}
{{- end }}
{{- end }}
export type DesignRunRequest = {
  designPressureBar: number;
  designTemperatureC: number;
  volumeM3: number;
  code: string;
};

export type DesignRunArtifact = {
  artifactId: string;
  artifactType: 'WorkflowExecutionReport.v1' | 'ComplianceDossierMachine.v1';
  location: string;
};

export type DesignRunResponse = {
  runId: string;
  workflowState: 'completed';
  complianceSummary: {
    status: 'pass';
    code: string;
    checksPassed: number;
    checksFailed: number;
  };
  artifacts: DesignRunArtifact[];
  source: 'frontend-placeholder' | 'backend-service';
};

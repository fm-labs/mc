import React from "react";
import { AxiosInstance } from "axios";
import { buildApiHttpClient } from "@/lib/api-http-client.ts";


const orchestraApiBuilder = (http: AxiosInstance) => {
  const getJobs = async (params: any) => {
    const response = await http.get("/api/celery/jobs", { params });
    return response.data;
  };

  const getJob = async (jobId: string) => {
    const response = await http.get(`/api/celery/jobs/${jobId}`);
    return response.data;
  };

  const getTask = async (taskId: string) => {
    const response = await http.get(`/api/celery/tasks/${taskId}`);
    return response.data;
  };

  const getAnsibleRuns = async (params: any) => {
    const response = await http.get("/api/ansible/runs", { params });
    return response.data;
  }

  const getAnsibleRun = async (runId: string) => {
    const response = await http.get(`/api/ansible/runs/${runId}`);
    return response.data;
  };

  return {
    getJobs,
    getJob,
    getTask,
    getAnsibleRuns,
    getAnsibleRun,
  };
};

export const useOrchestraApi = (baseUrl: string) => {
  return React.useMemo(() => {
      const apiHttpClient = buildApiHttpClient(baseUrl)
      return orchestraApiBuilder(apiHttpClient);
  }, []);
};

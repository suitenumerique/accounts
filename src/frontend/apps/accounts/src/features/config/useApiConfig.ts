import { useQuery } from "@tanstack/react-query";

import { fetchAPI } from "@/features/api/fetchApi";
import { Config } from "./types";

export function useApiConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: async (): Promise<Config> => {
      const response = await fetchAPI("config/");
      return response.json();
    },
    staleTime: 1000 * 60 * 60,
  });
}

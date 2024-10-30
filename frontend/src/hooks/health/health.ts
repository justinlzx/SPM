import { useMutation } from "@tanstack/react-query";
import { healthCheck } from "./health.utils";

export const useHealthCheck = () => {
    return useMutation<string | undefined, Error, void>({
        mutationFn: healthCheck,
        onSuccess: async (status) => {
            console.log(status);
        },
        onError: (error) => {
            throw new Error(`Health check failed: ${error}`);
        },
    });
};
import { useMutation } from "@tanstack/react-query";
import { healthCheck } from "./health.utils";

export const useHealthCheck = () => {
    return useMutation<void, Error>({
        mutationFn: healthCheck,
        onSuccess: async () => {
            console.log("Health check OK");
        },
        onError: (error) => {
            throw new Error(`Health check failed: ${error}`);
        },
    });
};
import { useMutation } from "@tanstack/react-query";
import { getArrangementsByManager } from "./arrangement.utils";

export const useArrangement = () => {
    return useMutation<string | undefined, Error, number>({
        mutationFn: getArrangementsByManager,
        onError: (error) => {
            throw new Error(`Failed to get arrangements: ${error.message}`);
        },
    });
};
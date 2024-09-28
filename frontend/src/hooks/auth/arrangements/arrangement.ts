import { useMutation } from "@tanstack/react-query";
import { getArrangementsByManager } from "./arrangement.utils";
import { Request } from "./arrangement.utils";

type MutationVariables = {
  id: number;
  status: string;
}

export const useArrangement = () => {
    return useMutation<Request[] | undefined, Error, MutationVariables>({
        mutationFn: ({ id, status }) => getArrangementsByManager(id, status),
        onError: (error) => {
            throw new Error(`Failed to get arrangements: ${error.message}`);
        },
    });
};
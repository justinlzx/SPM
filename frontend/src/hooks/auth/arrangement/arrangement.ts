import { useMutation } from "@tanstack/react-query";
import { getArrangementsByManager, updateArrangement } from "./arrangement.utils";
import { TRequest } from "./arrangement.utils";

type TArrangement = {
  id: number;
  status: string;
}

type TUpdateArrangement = {
    updatedStatus: "approve" | "reject";
    arrangement_id: number;
}


export const useArrangement = () => {
    return useMutation<TRequest[] | undefined, Error, TArrangement>({
        mutationFn: ({ id, status }) => getArrangementsByManager(id, status),
        onError: (error) => {
            throw new Error(`Failed to get arrangements: ${error.message}`);
        },
    });
};

export const useUpdateArrangement = () => {
    return useMutation<string, Error, TUpdateArrangement>({
        mutationFn: async ({updatedStatus, arrangement_id}) => {
            const result = await updateArrangement(updatedStatus, arrangement_id);
            if (!result) {
                throw new Error('Update failed, no data returned');
            }
            return result;
        },
        onError: (error) => {
            throw new Error(`Failed to update arrangement: ${error.message}`);
        },
    });
};
import { useMutation } from "@tanstack/react-query";
import { getArrangementsByManager, TArrangementQuery, updateArrangement } from "./arrangement.utils";
import { TRequest } from "./arrangement.utils";



type TUpdateArrangement = {
    updatedStatus: "approve" | "reject";
    arrangement_id: number;
}


export const useArrangement = () => {
    return useMutation<TRequest[] | undefined, Error, TArrangementQuery>({
        mutationFn: ({ id, status, page, rowsPerPage, searchTerm }) => getArrangementsByManager({id, status,  page, rowsPerPage, searchTerm}),
        onError: (error) => {
            throw new Error(`Failed to get arrangements: ${error.message}`);
        },
    });
};

export const useUpdateArrangement = () => {
    return useMutation<string, Error, TUpdateArrangement>({
        mutationFn: async ({updatedStatus}) => {
            const result = await updateArrangement(updatedStatus);
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
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export type TRequest = {
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  update_datetime: string;
  approval_status: string;
  reason_description: string;
  batch_id: string | null;
};

export type TArrangementQuery = {
  id: number;
  status: string;
  page: number
  rowsPerPage: number
  searchTerm: string
}

export const getArrangementsByManager = async ({
    id: manager_id,
    status,
    page,
    rowsPerPage,
    searchTerm
}: TArrangementQuery):  Promise<TRequest[] | undefined> => {
    try {
        const response = await axios.get(`${BACKEND_URL}/arrangements/subordinates/${manager_id}`, {
            params: {
                status,
                page,
                rowsPerPage,
                searchTerm
            },
        });
        if (response.status === 200) {
            return response.data as TRequest[]
        }
    } catch (error: any) {
        return;
    }
};

export const updateArrangement = async (request: "approve" | "reject", arrangement_id: number): Promise<any| undefined>  => {
    // try {
        //TODO: double check endpoint
        // const response = await axios.put(`${BACKEND_URL}/arrangement/update`, request);
        // if (response.status === 200) {
        //     return response.data;
        // }
        console.log("updateArrangement", request);
        return true
    // } 
    // catch (error: any) {
    //     return
    // }
};
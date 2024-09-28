import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export type Request = {
  requester_staff_id: number;
  wfh_date: string;
  wfh_type: string;
  arrangement_id: number;
  update_datetime: string;
  approval_status: string;
  reason_description: string;
  batch_id: string | null;
};

export const getArrangementsByManager = async (manager_id: number, status: string):  Promise<Request[] | undefined> => {
    try {
        const response = await axios.get(`${BACKEND_URL}/arrangement/view/${manager_id}`, {
            params: {
                status,
            },
        });
        if (response.status === 200) {
            return response.data as Request[]
        }
    } catch (error: any) {
        return;
    }
};
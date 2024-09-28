import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const getArrangementsByManager = async (manager_id: number):  Promise<string | undefined> => {
    try {
        const response = await axios.get(`${BACKEND_URL}/arrangements/${manager_id}`);
        if (response.status === 200) {
            return response.data
        }
    } catch (error: any) {
        return ;
    }
};
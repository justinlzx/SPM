import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const healthCheck = async ():  Promise<string | undefined> => {
    try {
        const response = await axios.get(`${BACKEND_URL}/health`);
        if (response.status === 200) {
            return "Health check OK";
        }
    } catch (error: any) {
        return `Health check failed: ${error.message}`;
    }
};

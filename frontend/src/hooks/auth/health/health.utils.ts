export const healthCheck = async () => {
    try {
        const response = await fetch('/api/health');
        if (response.status === 200) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error(error);
    }
};
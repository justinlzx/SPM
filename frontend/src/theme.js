import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      500: '#00007B',
      600: '#002db3',
      700: '#002699',
      800: '#002080',
      900: '#001966',
    },
    secondary: {
      500: '#262626',
      600: '#1f1f1f',
      700: '#191919',
      800: '#121212',
      900: '#0c0c0c',
    },
    tertiary: {
      500: '#3399ff',
      600: '#2d88e6',
      700: '#2677cc',
      800: '#2066b3',
      900: '#1a5599',
    },
  },
});

export default theme;

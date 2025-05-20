import { createTheme } from '@mui/material/styles';

// 创建一个更美观的自定义主题
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      light: '#4dabf5',
      main: '#1976d2',
      dark: '#1565c0',
      contrastText: '#fff',
    },
    secondary: {
      light: '#ff4081',
      main: '#f50057',
      dark: '#c51162',
      contrastText: '#fff',
    },
    success: {
      main: '#2e7d32',
      light: '#4caf50',
      dark: '#1b5e20',
    },
    info: {
      main: '#0288d1',
      light: '#03a9f4',
      dark: '#01579b',
    },
    warning: {
      main: '#ed6c02',
      light: '#ff9800',
      dark: '#e65100',
    },
    error: {
      main: '#d32f2f',
      light: '#ef5350',
      dark: '#c62828',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#546e7a',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
  typography: {
    fontFamily: [
      '"Inter"',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    subtitle1: {
      fontSize: '0.875rem',
    },
    subtitle2: {
      fontSize: '0.75rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.75rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 1px -1px rgba(0,0,0,0.08),0px 1px 1px 0px rgba(0,0,0,0.04),0px 1px 3px 0px rgba(0,0,0,0.02)',
    '0px 3px 3px -2px rgba(0,0,0,0.08),0px 3px 4px 0px rgba(0,0,0,0.04),0px 1px 8px 0px rgba(0,0,0,0.02)',
    '0px 3px 5px -1px rgba(0,0,0,0.08),0px 5px 8px 0px rgba(0,0,0,0.04),0px 1px 14px 0px rgba(0,0,0,0.02)',
    '0px 4px 5px -2px rgba(0,0,0,0.08),0px 7px 10px 1px rgba(0,0,0,0.04),0px 2px 16px 1px rgba(0,0,0,0.02)',
    '0px 5px 5px -3px rgba(0,0,0,0.08),0px 8px 10px 1px rgba(0,0,0,0.04),0px 3px 14px 2px rgba(0,0,0,0.02)',
    '0px 4px 5px -2px rgba(0, 0, 0, 0.1), 0px 7px 10px 1px rgba(0, 0, 0, 0.04), 0px 2px 16px 1px rgba(0, 0, 0, 0.02)',
    '0px 5px 5px -3px rgba(0, 0, 0, 0.1), 0px 8px 10px 1px rgba(0, 0, 0, 0.04), 0px 3px 14px 2px rgba(0, 0, 0, 0.02)',
    '0px 5px 6px -3px rgba(0, 0, 0, 0.1), 0px 9px 12px 1px rgba(0, 0, 0, 0.04), 0px 3px 16px 2px rgba(0, 0, 0, 0.02)',
    '0px 6px 6px -3px rgba(0, 0, 0, 0.1), 0px 10px 14px 1px rgba(0, 0, 0, 0.04), 0px 4px 18px 3px rgba(0, 0, 0, 0.02)',
    '0px 6px 7px -4px rgba(0, 0, 0, 0.1), 0px 11px 15px 1px rgba(0, 0, 0, 0.04), 0px 4px 20px 3px rgba(0, 0, 0, 0.02)',
    '0px 7px 8px -4px rgba(0, 0, 0, 0.1), 0px 12px 17px 2px rgba(0, 0, 0, 0.04), 0px 5px 22px 4px rgba(0, 0, 0, 0.02)',
    '0px 7px 8px -4px rgba(0, 0, 0, 0.1), 0px 13px 19px 2px rgba(0, 0, 0, 0.04), 0px 5px 24px 4px rgba(0, 0, 0, 0.02)',
    '0px 7px 9px -4px rgba(0, 0, 0, 0.1), 0px 14px 21px 2px rgba(0, 0, 0, 0.04), 0px 5px 26px 4px rgba(0, 0, 0, 0.02)',
    '0px 8px 9px -5px rgba(0, 0, 0, 0.1), 0px 15px 22px 2px rgba(0, 0, 0, 0.04), 0px 6px 28px 5px rgba(0, 0, 0, 0.02)',
    '0px 8px 10px -5px rgba(0, 0, 0, 0.1), 0px 16px 24px 2px rgba(0, 0, 0, 0.04), 0px 6px 30px 5px rgba(0, 0, 0, 0.02)',
    '0px 8px 11px -5px rgba(0, 0, 0, 0.1), 0px 17px 26px 2px rgba(0, 0, 0, 0.04), 0px 6px 32px 5px rgba(0, 0, 0, 0.02)',
    '0px 9px 11px -5px rgba(0, 0, 0, 0.1), 0px 18px 28px 2px rgba(0, 0, 0, 0.04), 0px 7px 34px 6px rgba(0, 0, 0, 0.02)',
    '0px 9px 12px -6px rgba(0, 0, 0, 0.1), 0px 19px 29px 2px rgba(0, 0, 0, 0.04), 0px 7px 36px 6px rgba(0, 0, 0, 0.02)',
    '0px 10px 13px -6px rgba(0, 0, 0, 0.1), 0px 20px 31px 3px rgba(0, 0, 0, 0.04), 0px 8px 38px 7px rgba(0, 0, 0, 0.02)',
    '0px 10px 13px -6px rgba(0, 0, 0, 0.1), 0px 21px 33px 3px rgba(0, 0, 0, 0.04), 0px 8px 40px 7px rgba(0, 0, 0, 0.02)',
    '0px 10px 14px -6px rgba(0, 0, 0, 0.1), 0px 22px 35px 3px rgba(0, 0, 0, 0.04), 0px 8px 42px 7px rgba(0, 0, 0, 0.02)',
    '0px 11px 14px -7px rgba(0, 0, 0, 0.1), 0px 23px 36px 3px rgba(0, 0, 0, 0.04), 0px 9px 44px 8px rgba(0, 0, 0, 0.02)',
    '0px 11px 15px -7px rgba(0, 0, 0, 0.1), 0px 24px 38px 3px rgba(0, 0, 0, 0.04), 0px 9px 46px 8px rgba(0, 0, 0, 0.02)'
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        html: {
          scrollBehavior: 'smooth',
        },
        '::selection': {
          backgroundColor: '#1976d2',
          color: '#fff',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
          },
        },
        contained: {
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.06)',
        },
        elevation2: {
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0px 6px 16px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          overflow: 'hidden',
          transition: '0.3s',
          '&:hover': {
            boxShadow: '0px 8px 20px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          '&:last-child': {
            paddingBottom: 16,
          },
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-root': {
            fontWeight: 600,
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0px 1px 4px rgba(0, 0, 0, 0.05)',
          backgroundImage: 'linear-gradient(to right, #1976d2, #2196f3)',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(0, 0, 0, 0.23)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderWidth: 1,
          },
        },
        notchedOutline: {
          borderColor: 'rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#ffffff',
          backgroundImage: 'none',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: 'rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '4px 8px',
          paddingLeft: 16,
          paddingRight: 16,
          '&.Mui-selected': {
            backgroundColor: 'rgba(25, 118, 210, 0.08)',
            '&:hover': {
              backgroundColor: 'rgba(25, 118, 210, 0.15)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          minWidth: 40,
          color: 'inherit',
        },
      },
    },
  },
});

export default theme; 
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardHeader from '@mui/material/CardHeader';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { ArrowRight } from '@phosphor-icons/react';
import { SxProps } from '@mui/material/styles';
import dayjs from 'dayjs';

const statusMap = {
  pending: { label: 'Pending', color: 'warning' },
  approved: { label: 'Approved', color: 'success' },
  rejected: { label: 'Rejected', color: 'error' },
} as const;

export interface Request {
  id: number;
  wfh_type: 'am' | 'pm' | 'full';
  startDate: Date;
  endDate: Date;
  status: 'pending' | 'approved' | 'rejected';
}

export interface LatestRequestProps {
  sx?: SxProps;
}

export const RequestList = ({ sx }: LatestRequestProps): React.JSX.Element => {
  // Hardcoded WFH data
  const hardcodedRequests: Request[] = [
    {
      id: 1234,
      wfh_type: 'full',
      startDate: new Date('2023-09-25'),
      endDate: new Date('2023-09-25'),
      status: 'pending',
    },
    {
      id: 1235,
      wfh_type: 'am',
      startDate: new Date('2023-09-26'),
      endDate: new Date('2023-09-26'),
      status: 'approved',
    },
    {
      id: 1236,
      wfh_type: 'pm',
      startDate: new Date('2023-09-27'),
      endDate: new Date('2023-09-27'),
      status: 'rejected',
    },
  ];

  return (
    <Card sx={sx}>
      <CardHeader title="Latest WFH Requests" />
      <Divider />
      <Box sx={{ overflowX: 'auto' }}>
        <Table sx={{ minWidth: 800 }}>
          <TableHead>
            <TableRow>
              <TableCell>Request</TableCell>
              <TableCell>WFH Type</TableCell>
              <TableCell>Start Date</TableCell>
              <TableCell>End Date</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hardcodedRequests.map((request) => {
              const { label, color } = statusMap[request.status] ?? { label: 'Unknown', color: 'default' };

              return (
                <TableRow hover key={request.id}>
                  <TableCell>{request.id}</TableCell>
                  <TableCell>{request.wfh_type.toUpperCase()}</TableCell>
                  <TableCell>{dayjs(request.startDate).format('MMM D, YYYY')}</TableCell>
                  <TableCell>{dayjs(request.endDate).format('MMM D, YYYY')}</TableCell>
                  <TableCell>
                    <Chip color={color} label={label} size="small" />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Box>
      <Divider />
      <CardActions sx={{ justifyContent: 'flex-end' }}>
        <Button
          color="inherit"
          endIcon={<ArrowRight fontSize="var(--icon-fontSize-md)" />}
          size="small"
          variant="text"
        >
          View all
        </Button>
      </CardActions>
    </Card>
  );
};

export default RequestList;

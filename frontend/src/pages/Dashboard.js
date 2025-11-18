import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  ToggleButton,
  ToggleButtonGroup,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  Receipt as ReceiptIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { analyticsAPI } from '../services/api';
import { format, subMonths, startOfMonth, endOfMonth } from 'date-fns';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [spendingByCategory, setSpendingByCategory] = useState([]);
  const [timeSeries, setTimeSeries] = useState([]);
  const [chartType, setChartType] = useState('pie');
  const [timeGranularity, setTimeGranularity] = useState('monthly');
  const [dateRange, setDateRange] = useState('3months');

  useEffect(() => {
    loadDashboardData();
  }, [dateRange, timeGranularity]);

  const getDateRangeParams = () => {
    const today = new Date();
    let startDate, endDate;

    switch (dateRange) {
      case 'thisMonth':
        startDate = startOfMonth(today);
        endDate = endOfMonth(today);
        break;
      case 'lastMonth':
        const lastMonth = subMonths(today, 1);
        startDate = startOfMonth(lastMonth);
        endDate = endOfMonth(lastMonth);
        break;
      case '3months':
        startDate = subMonths(today, 3);
        endDate = today;
        break;
      case '6months':
        startDate = subMonths(today, 6);
        endDate = today;
        break;
      case '12months':
        startDate = subMonths(today, 12);
        endDate = today;
        break;
      default:
        startDate = subMonths(today, 3);
        endDate = today;
    }

    return {
      start_date: format(startDate, 'yyyy-MM-dd'),
      end_date: format(endDate, 'yyyy-MM-dd'),
    };
  };

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const params = getDateRangeParams();

      const [summaryRes, categoryRes, timeSeriesRes] = await Promise.all([
        analyticsAPI.getSummary(params),
        analyticsAPI.getSpendingByCategory(params),
        analyticsAPI.getSpendingTimeSeries({ ...params, group_by: timeGranularity }),
      ]);

      setSummary(summaryRes.data);
      setSpendingByCategory(categoryRes.data);
      setTimeSeries(timeSeriesRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const pieChartData = {
    labels: spendingByCategory.map(c => c.category_name),
    datasets: [{
      data: spendingByCategory.map(c => c.total_amount),
      backgroundColor: [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
      ],
    }],
  };

  const barChartData = {
    labels: spendingByCategory.map(c => c.category_name),
    datasets: [{
      label: 'Spending by Category',
      data: spendingByCategory.map(c => c.total_amount),
      backgroundColor: '#36A2EB',
    }],
  };

  const timeSeriesChartData = {
    labels: timeSeries.map(t => t.period),
    datasets: [{
      label: 'Total Spending',
      data: timeSeries.map(t => t.total_amount),
      borderColor: '#36A2EB',
      backgroundColor: 'rgba(54, 162, 235, 0.2)',
      tension: 0.4,
    }],
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Date Range Selector */}
      <Box sx={{ mb: 3 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Date Range</InputLabel>
          <Select value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
            <MenuItem value="thisMonth">This Month</MenuItem>
            <MenuItem value="lastMonth">Last Month</MenuItem>
            <MenuItem value="3months">Last 3 Months</MenuItem>
            <MenuItem value="6months">Last 6 Months</MenuItem>
            <MenuItem value="12months">Last 12 Months</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon color="primary" sx={{ mr: 1 }} />
                <Typography color="text.secondary" variant="h6">
                  Total Spending
                </Typography>
              </Box>
              <Typography variant="h4">
                ${summary?.total_spending?.toFixed(2) || '0.00'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ReceiptIcon color="primary" sx={{ mr: 1 }} />
                <Typography color="text.secondary" variant="h6">
                  Transactions
                </Typography>
              </Box>
              <Typography variant="h4">
                {summary?.transaction_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingIcon color="primary" sx={{ mr: 1 }} />
                <Typography color="text.secondary" variant="h6">
                  Top Category
                </Typography>
              </Box>
              <Typography variant="h6">
                {summary?.top_categories?.[0]?.category_name || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ${summary?.top_categories?.[0]?.total_amount?.toFixed(2) || '0.00'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Category Spending Chart */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Spending by Category</Typography>
              <ToggleButtonGroup
                size="small"
                value={chartType}
                exclusive
                onChange={(e, value) => value && setChartType(value)}
              >
                <ToggleButton value="pie">Pie</ToggleButton>
                <ToggleButton value="bar">Bar</ToggleButton>
              </ToggleButtonGroup>
            </Box>
            {chartType === 'pie' ? (
              <Pie data={pieChartData} options={{ maintainAspectRatio: true }} />
            ) : (
              <Bar data={barChartData} options={{ maintainAspectRatio: true }} />
            )}
          </Paper>
        </Grid>

        {/* Time Series Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Spending Over Time</Typography>
              <ToggleButtonGroup
                size="small"
                value={timeGranularity}
                exclusive
                onChange={(e, value) => value && setTimeGranularity(value)}
              >
                <ToggleButton value="daily">Daily</ToggleButton>
                <ToggleButton value="weekly">Weekly</ToggleButton>
                <ToggleButton value="monthly">Monthly</ToggleButton>
              </ToggleButtonGroup>
            </Box>
            <Line data={timeSeriesChartData} options={{ maintainAspectRatio: true }} />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;

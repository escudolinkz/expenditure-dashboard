import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Line, Bar } from 'react-chartjs-2';
import { analyticsAPI } from '../services/api';
import { format, subMonths } from 'date-fns';

function Reports() {
  const [timeSeries, setTimeSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [granularity, setGranularity] = useState('monthly');
  const [chartType, setChartType] = useState('line');
  const [includeCategories, setIncludeCategories] = useState(false);
  const [startDate, setStartDate] = useState(subMonths(new Date(), 12));
  const [endDate, setEndDate] = useState(new Date());

  useEffect(() => {
    loadReport();
  }, [granularity, startDate, endDate, includeCategories]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const params = {
        group_by: granularity,
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
        include_categories: includeCategories,
      };

      const response = await analyticsAPI.getSpendingTimeSeries(params);
      setTimeSeries(response.data);
    } catch (error) {
      console.error('Error loading report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const params = {
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
      };

      const response = await analyticsAPI.exportCSV(params);

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions_${format(new Date(), 'yyyyMMdd')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  const chartData = {
    labels: timeSeries.map(t => t.period),
    datasets: includeCategories && timeSeries[0]?.categories
      ? // Stacked chart with categories
        (() => {
          const categoryMap = {};
          timeSeries.forEach(period => {
            period.categories?.forEach(cat => {
              if (!categoryMap[cat.category_name]) {
                categoryMap[cat.category_name] = {
                  label: cat.category_name,
                  data: [],
                  backgroundColor: `hsl(${Math.random() * 360}, 70%, 60%)`,
                };
              }
            });
          });

          Object.keys(categoryMap).forEach(catName => {
            timeSeries.forEach(period => {
              const cat = period.categories?.find(c => c.category_name === catName);
              categoryMap[catName].data.push(cat ? cat.total_amount : 0);
            });
          });

          return Object.values(categoryMap);
        })()
      : // Simple total spending
        [{
          label: 'Total Spending',
          data: timeSeries.map(t => t.total_amount),
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          tension: 0.4,
        }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      x: {
        stacked: includeCategories,
      },
      y: {
        stacked: includeCategories,
        ticks: {
          callback: function(value) {
            return '$' + value.toFixed(0);
          }
        }
      }
    },
    plugins: {
      legend: {
        display: includeCategories,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            label += '$' + context.parsed.y.toFixed(2);
            return label;
          }
        }
      }
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Reports
        </Typography>

        {/* Controls */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Granularity</InputLabel>
                <Select value={granularity} onChange={(e) => setGranularity(e.target.value)}>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={2}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>

            <Grid item xs={12} md={2}>
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <ToggleButtonGroup
                value={chartType}
                exclusive
                onChange={(e, value) => value && setChartType(value)}
                fullWidth
              >
                <ToggleButton value="line">Line</ToggleButton>
                <ToggleButton value="bar">Bar</ToggleButton>
              </ToggleButtonGroup>
            </Grid>

            <Grid item xs={12} md={3}>
              <Button
                variant={includeCategories ? 'contained' : 'outlined'}
                onClick={() => setIncludeCategories(!includeCategories)}
                fullWidth
              >
                {includeCategories ? 'Hide Categories' : 'Show Categories'}
              </Button>
            </Grid>
          </Grid>

          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" onClick={handleExportCSV}>
              Export to CSV
            </Button>
          </Box>
        </Paper>

        {/* Chart */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Spending Over Time
          </Typography>
          {chartType === 'line' ? (
            <Line data={chartData} options={chartOptions} />
          ) : (
            <Bar data={chartData} options={chartOptions} />
          )}
        </Paper>

        {/* Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Period</TableCell>
                <TableCell align="right">Total Spending</TableCell>
                <TableCell align="right">Transactions</TableCell>
                {includeCategories && <TableCell>Top Categories</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {timeSeries.map((period) => (
                <TableRow key={period.period}>
                  <TableCell>{period.period}</TableCell>
                  <TableCell align="right">${parseFloat(period.total_amount).toFixed(2)}</TableCell>
                  <TableCell align="right">{period.transaction_count}</TableCell>
                  {includeCategories && (
                    <TableCell>
                      {period.categories?.slice(0, 3).map((cat) => (
                        <Box key={cat.category_name} component="span" sx={{ mr: 2 }}>
                          {cat.category_name}: ${parseFloat(cat.total_amount).toFixed(2)}
                        </Box>
                      ))}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Container>
    </LocalizationProvider>
  );
}

export default Reports;

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab
} from '@mui/material';

// TabPanel组件
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`rule-helper-tabpanel-${index}`}
      aria-labelledby={`rule-helper-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 2, pb: 1 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// 交易类型示例规则
const EXAMPLE_RULES = {
  'stock-in': [
    // 规则类型1 - 通用入库识别规则
    {
      ruleName: '通用入库识别规则',
      rules: [
        {
          field: 'item_name',
          regex: '[品名|物品|道具]+[^：:]*[：:]*\\s*(.+)$',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"物品：灵之精火"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '[数量|个数|件数]+[^：:]*[：:]*\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"数量：66"中的"66"'
        },
        {
          field: 'unit_price',
          regex: '[价格|金额|花费]+[^：:]*[：:]*\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配单价，例如"价格：1188"中的"1188"'
        }
      ]
    },
    // 规则类型2 - 精确入库识别规则
    {
      ruleName: '精确入库识别规则',
      rules: [
        {
          field: 'item_name',
          regex: '获得了(.+?)×',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"获得了灵之精火×66"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '×(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"获得了灵之精火×66"中的"66"'
        },
        {
          field: 'unit_price',
          regex: '失去了银两×(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配花费，例如"失去了银两×1188"中的"1188"'
        }
      ]
    }
  ],
  'stock-out': [
    // 规则类型1 - 通用出库识别规则
    {
      ruleName: '通用出库识别规则',
      rules: [
        {
          field: 'item_name',
          regex: '[品名|物品名称|道具]+[^：:]*[：:]*\\s*(.+)$',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"物品名称：灵之精火"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '[数量|个数|件数]+[^：:]*[：:]*\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"数量：66"中的"66"'
        },
        {
          field: 'unit_price',
          regex: '[单价|价格]+[^：:]*[：:]*\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配单价，例如"单价：1188"中的"1188"'
        },
        {
          field: 'fee',
          regex: '[手续费|费用]+[^：:]*[：:]*\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配手续费，例如"手续费：3921"中的"3921"'
        }
      ]
    },
    // 规则类型2 - 售出确认识别规则
    {
      ruleName: '售出确认识别规则',
      rules: [
        {
          field: 'item_name',
          regex: '已成功售出([^（(]+)[（(]',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"已成功售出灵之精火（66）"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '[（(](\\d+)[）)]',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"已成功售出灵之精火（66）"中的"66"'
        },
        {
          field: 'unit_price',
          regex: '售出单价[：:]\\s*(\\d+)银两',
          group: 1,
          default_value: '0',
          description: '匹配单价，例如"售出单价：1188银两"中的"1188"'
        },
        {
          field: 'fee',
          regex: '手续费[：:]\\s*(\\d+)银两',
          group: 1,
          default_value: '0',
          description: '匹配手续费，例如"手续费：3921银两"中的"3921"'
        }
      ]
    },
    // 规则类型3 - 售出通知识别规则
    {
      ruleName: '售出通知识别规则',
      rules: [
        {
          field: 'quantity',
          regex: '已成功售出(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"已成功售出60诛仙古玉"中的"60"'
        },
        {
          field: 'item_name',
          regex: '已成功售出\\d+([^，,。]+)[，,。]',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"已成功售出60诛仙古玉，请在附件中领取..."中的"诛仙古玉"'
        },
        {
          field: 'total_amount',
          regex: '(\\d+)\\s*$',
          group: 1,
          default_value: '0',
          description: '匹配总金额，例如文本末尾的数字"136116"'
        }
      ]
    }
  ],
  'monitor': [
    {
      ruleName: '摆摊物品监控规则',
      rules: [
        {
          field: 'item_name',
          regex: '物品[:：]\\s*([^\\n]+)',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"物品：灵之精火"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '数量[:：]\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"数量：66"中的"66"'
        },
        {
          field: 'market_price',
          regex: '一口价[:：]\\s*(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配价格，例如"一口价：1188"中的"1188"'
        },
        {
          field: 'note',
          regex: '备注[:：]\\s*([^\\n]+)',
          group: 1,
          default_value: '',
          description: '匹配备注，例如"备注：批发价"中的"批发价"'
        }
      ]
    },
    {
      ruleName: '寄售行物品监控规则',
      rules: [
        {
          field: 'item_name',
          regex: '名称[:：]\\s*([^\\n]+)',
          group: 1,
          default_value: '',
          description: '匹配物品名称，例如"名称：灵之精火"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '数量[:：]\\s*(\\d+)\\s',
          group: 1,
          default_value: '0',
          description: '匹配数量，例如"数量：66"中的"66"'
        },
        {
          field: 'market_price',
          regex: '售价[:：]\\s*(\\d+)\\s',
          group: 1,
          default_value: '0',
          description: '匹配价格，例如"售价：1188"中的"1188"'
        },
        {
          field: 'server',
          regex: '服务器[:：]\\s*([^\\n]+)',
          group: 1,
          default_value: '',
          description: '匹配服务器，例如"服务器：飞龙在天"中的"飞龙在天"'
        }
      ]
    },
    {
      ruleName: '表格数据监控规则',
      rules: [
        {
          field: 'item_name',
          regex: '^\\s*([^\\d\\n]+?)\\s+\\d',
          group: 1,
          default_value: '',
          description: '匹配表格中的物品名称，例如"灵之精火    66    1188"中的"灵之精火"'
        },
        {
          field: 'quantity',
          regex: '^\\s*[^\\d\\n]+?\\s+(\\d+)\\s+\\d',
          group: 1,
          default_value: '0',
          description: '匹配表格中的数量，例如"灵之精火    66    1188"中的"66"'
        },
        {
          field: 'market_price',
          regex: '^\\s*[^\\d\\n]+?\\s+\\d+\\s+(\\d+)',
          group: 1,
          default_value: '0',
          description: '匹配表格中的价格，例如"灵之精火    66    1188"中的"1188"'
        }
      ]
    }
  ]
};

/**
 * OCR规则帮助对话框组件
 */
function OCRRuleHelperDialog({ open, onClose, transactionType }) {
  const [activeTab, setActiveTab] = React.useState(0);
  const [activeRuleIndex, setActiveRuleIndex] = React.useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setActiveRuleIndex(0); // 切换标签时重置当前选中的规则
  };

  const handleRuleChange = (event, newValue) => {
    setActiveRuleIndex(newValue);
  };

  // 获取当前类型的规则列表
  const currentTypeRules = EXAMPLE_RULES[transactionType] || EXAMPLE_RULES['stock-in'];
  
  // 获取当前选中的规则
  const currentRule = currentTypeRules[activeRuleIndex] || currentTypeRules[0];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>OCR规则帮助</DialogTitle>
      <DialogContent>
        <Typography variant="subtitle1" gutterBottom>
          规则说明
        </Typography>
        <Typography variant="body2" paragraph>
          OCR规则使用正则表达式从识别文本中提取关键信息。每条规则包含以下部分：
        </Typography>
        <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>字段</TableCell>
                <TableCell>说明</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>字段名</TableCell>
                <TableCell>映射到系统中的字段名称，如：item_name, quantity, unit_price等</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>正则表达式</TableCell>
                <TableCell>用于匹配文本的模式，括号()表示要提取的内容</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>组序号</TableCell>
                <TableCell>指定使用正则表达式的第几个匹配组，通常为1（第一个括号内的内容）</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>默认值</TableCell>
                <TableCell>当无法匹配到内容时使用的默认值</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <Typography variant="subtitle1" gutterBottom>
          规则示例
        </Typography>
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="入库规则" />
            <Tab label="出库规则" />
            <Tab label="监控规则" />
          </Tabs>
        </Box>
        
        {/* 如果当前类型有多个规则，显示子标签 */}
        {currentTypeRules.length > 1 && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 2 }}>
            <Tabs 
              value={activeRuleIndex} 
              onChange={handleRuleChange}
              variant="scrollable"
              scrollButtons="auto"
            >
              {currentTypeRules.map((rule, index) => (
                <Tab key={index} label={rule.ruleName} />
              ))}
            </Tabs>
          </Box>
        )}
        
        <TabPanel value={activeTab} index={0}>
          <Typography variant="body2" paragraph>
            入库规则示例（{currentRule.ruleName}）:
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>字段名</TableCell>
                  <TableCell>正则表达式</TableCell>
                  <TableCell>组序号</TableCell>
                  <TableCell>默认值</TableCell>
                  <TableCell>说明</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentTypeRules[activeRuleIndex].rules.map((rule, index) => (
                  <TableRow key={index}>
                    <TableCell>{rule.field}</TableCell>
                    <TableCell><code>{rule.regex}</code></TableCell>
                    <TableCell>{rule.group}</TableCell>
                    <TableCell>{rule.default_value}</TableCell>
                    <TableCell>{rule.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
        
        <TabPanel value={activeTab} index={1}>
          <Typography variant="body2" paragraph>
            出库规则示例（{currentRule.ruleName}）:
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>字段名</TableCell>
                  <TableCell>正则表达式</TableCell>
                  <TableCell>组序号</TableCell>
                  <TableCell>默认值</TableCell>
                  <TableCell>说明</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentTypeRules[activeRuleIndex].rules.map((rule, index) => (
                  <TableRow key={index}>
                    <TableCell>{rule.field}</TableCell>
                    <TableCell><code>{rule.regex}</code></TableCell>
                    <TableCell>{rule.group}</TableCell>
                    <TableCell>{rule.default_value}</TableCell>
                    <TableCell>{rule.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
        
        <TabPanel value={activeTab} index={2}>
          <Typography variant="body2" paragraph>
            监控规则示例（{currentRule.ruleName}）:
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>字段名</TableCell>
                  <TableCell>正则表达式</TableCell>
                  <TableCell>组序号</TableCell>
                  <TableCell>默认值</TableCell>
                  <TableCell>说明</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentTypeRules[activeRuleIndex].rules.map((rule, index) => (
                  <TableRow key={index}>
                    <TableCell>{rule.field}</TableCell>
                    <TableCell><code>{rule.regex}</code></TableCell>
                    <TableCell>{rule.group}</TableCell>
                    <TableCell>{rule.default_value}</TableCell>
                    <TableCell>{rule.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}

export default OCRRuleHelperDialog; 
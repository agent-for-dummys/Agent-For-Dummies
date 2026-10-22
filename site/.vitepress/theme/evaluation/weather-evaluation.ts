export type ScenarioId = 'success' | 'wrong-city' | 'wrong-answer' | 'timeout';
export interface Check { label: string; passed: boolean; evidence: string; step: number }
export interface Weather { city: string; condition: string; temperature: number }
export interface Diagnosis { step: number; title: string; reason: string; fix: string }
export interface EvaluationRun {
  city: string;
  weather: Weather | null;
  answer: string;
  checks: Check[];
  diagnosis: Diagnosis | null;
  queryCompleted: boolean;
}

export const question = '查询杭州当前天气，并告诉我要不要带伞。';
export const scenarios: {id: ScenarioId; label: string}[] = [
  {id: 'success', label: '正常完成'},
  {id: 'wrong-city', label: '传错城市'},
  {id: 'wrong-answer', label: '回答温度出错'},
  {id: 'timeout', label: '接口超时'},
];
export const steps = [
  {title: '用户输入', kind: 'input'},
  {title: '工具调用', kind: 'call'},
  {title: '工具返回', kind: 'result'},
  {title: '生成回答', kind: 'answer'},
  {title: '逐项评测', kind: 'evaluate'},
] as const;

export function createRun(scenario: ScenarioId, repaired: boolean): EvaluationRun {
  const wrongCity = scenario === 'wrong-city' && !repaired;
  const wrongAnswer = scenario === 'wrong-answer' && !repaired;
  const timeout = scenario === 'timeout';
  const city = wrongCity ? '北京' : '杭州';
  const weather = timeout ? null : {
    city, condition: wrongCity ? '晴' : '小雨', temperature: wrongCity ? 20 : 18,
  };
  let answer = `${city}目前${weather?.condition}，气温为 ${wrongAnswer ? 28 : weather?.temperature}℃。${wrongCity ? '天气晴朗，暂时无需带伞。' : '有小雨，出门记得带伞。'}`;
  if (timeout) answer = repaired
    ? '天气服务请求超时，暂时无法查询杭州的天气，请稍后重试。'
    : '杭州目前晴，气温为 22℃，出门不用带伞。';

  const checks: Check[] = timeout ? [
    {label: '明确说明天气查询失败', passed: repaired, evidence: repaired ? '回答说明了天气服务超时。' : '工具返回了超时错误，回答却声称查询到了天气。', step: 3},
    {label: '缺少数据时不编造天气和温度', passed: repaired, evidence: repaired ? '回答没有提供未经查询的天气或温度。' : '工具没有返回天气，回答中的“晴、22℃”缺少依据。', step: 3},
  ] : [
    {label: '工具参数使用用户要求的城市', passed: !wrongCity, evidence: wrongCity ? '用户要求杭州，工具参数却是北京。' : '用户要求杭州，city 参数也是杭州。', step: 1},
    {label: '最终回答对应用户要求的城市', passed: !wrongCity, evidence: wrongCity ? '回答的是北京的天气，无法完成杭州的查询。' : '回答中的城市为杭州。', step: 3},
    {label: '回答天气和温度与工具结果一致', passed: !wrongAnswer, evidence: wrongAnswer ? '工具返回 18℃，回答却写成了 28℃。' : `工具返回${weather!.condition}、${weather!.temperature}℃，回答与之相符。`, step: 3},
    {label: '带伞建议符合查到的天气', passed: true, evidence: wrongCity ? '晴天与无需带伞的建议一致，但城市错误仍然会使整个任务失败。' : '工具返回小雨，回答建议带伞。', step: 3},
  ];

  let diagnosis: Diagnosis | null = null;
  if (wrongCity) diagnosis = {
    step: 1, title: '城市从工具调用开始出错',
    reason: '输入中是杭州，city 却被填成北京。工具正常返回了北京天气，后面的回答沿用了这个错误城市。',
    fix: '生成工具参数时保留用户指定的城市，将 city 改回“杭州”，再用同一条任务重新评测。',
  };
  if (wrongAnswer) diagnosis = {
    step: 3, title: '温度在生成回答时被改写',
    reason: '工具参数和返回结果都正确，18℃在最终回答中变成了 28℃，需要检查读取工具结果和生成回答的环节。',
    fix: '回答使用工具返回的 temperature，不额外改写数值，再检查回答与工具结果是否一致。',
  };
  if (timeout && !repaired) diagnosis = {
    step: 3, title: '接口超时后，回答仍然编造了天气',
    reason: '工具返回的是 TimeoutError，天气服务没有提供数据。随后生成的“晴、22℃”暴露了异常处理的问题。',
    fix: '捕获超时并明确说明查询失败，停止生成没有数据支持的天气信息。重新评测异常处理是否正确。',
  };
  return {
    city, weather, answer, checks, diagnosis, queryCompleted: !timeout && !wrongCity && !wrongAnswer,
  };
}

export type WalkthroughKind = 'attention' | 'multi-head' | 'transformer' | 'mask' | 'padding';
export const tokens = ['我', '喜欢', '你'];
export const inputs = [[1, 0], [0, 1], [1, 1]];
const identity = [[1, 0], [0, 1]];
const valueProjection = [[1, 1], [0, 1]];
export const format = (value: number) => Number(value.toFixed(3)).toString();
export const vectorText = (vector: number[]) => `[${vector.map(format).join(', ')}]`;

export function project(matrix: number[][], vector: number[]) {
  return matrix.map(row => row.reduce((sum, value, i) => sum + value * vector[i], 0));
}

export function attention(queryIndex: number, causal = false, wq = identity, wk = identity, wv = valueProjection) {
  const queries = inputs.map(vector => project(wq, vector));
  const keys = inputs.map(vector => project(wk, vector));
  const values = inputs.map(vector => project(wv, vector));
  const query = queries[queryIndex];
  const scores = keys.map(key => key.reduce((sum, value, i) => sum + value * query[i], 0));
  const scaled = scores.map(score => score / Math.sqrt(query.length));
  const masked = scaled.map((score, i) => causal && i > queryIndex ? -Infinity : score);
  const maximum = Math.max(...masked);
  const exponents = masked.map(score => Math.exp(score - maximum));
  const total = exponents.reduce((sum, value) => sum + value, 0);
  const weights = exponents.map(value => value / total);
  const weighted = values.map((vector, i) => vector.map(value => value * weights[i]));
  const output = weighted.reduce((sum, vector) => sum.map((value, i) => value + vector[i]), [0, 0]);
  return { queries, keys, values, query, scores, scaled, masked, weights, weighted, output };
}

export function multiHead(queryIndex: number) {
  const first = attention(queryIndex, false, identity, identity, identity);
  const second = attention(queryIndex, false, [[0, 1], [1, 0]], identity, [[1, 1], [1, -1]]);
  const concatenated = [...first.output, ...second.output];
  const output = project([[1, 0, .5, 0], [0, 1, 0, .5]], concatenated);
  return { first, second, concatenated, output };
}

export const walkthroughs: Record<WalkthroughKind, { title: string; steps: { title: string; description: string }[] }> = {
  attention: { title: 'Self-Attention 交互图解', steps: [
    { title: '输入', description: '每个词的向量占一列，组成输入矩阵 X。' },
    { title: 'QKV', description: '同一个输入，经三组共享的投影矩阵，得到 Q、K、V。' },
    { title: '打分', description: 'Key 的一行乘 Query 的一列，得到一个匹配分数。' },
    { title: '缩放', description: '点积分数除以 √dₖ。' },
    { title: '权重', description: '对每个 Query 的分数做 Softmax；每列权重之和为 1。' },
    { title: '汇总', description: '权重乘 Value，再相加，得到当前词的新表示。' }
  ] },
  'multi-head': { title: '多头注意力交互图解', steps: [
    { title: '投影', description: '同一输入，两个头各用自己的 Q、K、V 参数。' },
    { title: '并行', description: '每个头独立计算权重，再加权汇总自己的 Value。' },
    { title: '拼接', description: '沿特征维拼接各个头的输出。' },
    { title: '输出', description: 'Wᴼ 混合各个头的信息，将结果映射回模型维度。' }
  ] },
  transformer: { title: 'Transformer 交互图解', steps: [
    { title: '位置', description: '词嵌入加位置编码，保留词序信息。' },
    { title: '注意力', description: 'Encoder 的每个位置都可以参考其他有效位置。' },
    { title: '残差', description: '原论文采用 Post-LN：先加回输入，再做 LayerNorm。' },
    { title: 'Enc FFN', description: 'FFN 分别加工每个位置，然后做 Add & Norm。' },
    { title: '遮罩', description: 'Decoder 只能参考当前和过去，不能偷看未来。' },
    { title: '交叉', description: 'Q 来自 Decoder；K、V 来自 Encoder 的最终输出。' },
    { title: 'Dec FFN', description: '交叉注意力后，经过 FFN 和 Add & Norm。' },
    { title: '输出', description: 'Linear 和 Softmax 给出下一词的概率。' }
  ] },
  mask: { title: 'Masked Attention 逐词计算', steps: [
    { title: '我', description: '“我”的输出只读取自身，后两个词被遮住。' },
    { title: '喜欢', description: '“喜欢”的输出读取前两个词，“你”被遮住。' },
    { title: '你', description: '“你”的输出可以读取全部三个词。' }
  ] },
  padding: { title: 'Padding Mask', steps: [
    { title: '不同句长', description: '同一个 batch 中，三个句子的长度分别是 4、3、1。' },
    { title: '补齐 PAD', description: '补成相同长度，组成 3 × 4 的矩阵。' },
    { title: '屏蔽 PAD', description: '真实词保留；PAD 位置不被关注，注意力权重为 0。' }
  ] }
};

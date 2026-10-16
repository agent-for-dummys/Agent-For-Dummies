declare module 'virtual:pytorch-content' {
  const content: {
    lessons: Record<string, string>;
    problems: Record<string, { statement: string; formula: string; analysis: string[]; limits:string[]; parameters:string[]; returns:string; explanations:string[] }>;
  };
  export default content;
}

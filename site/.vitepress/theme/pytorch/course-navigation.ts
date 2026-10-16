export type Track = 'agent' | 'pytorch';
export interface NavigationState { selected: string; completed: string[] }
export interface CatalogItem { id: string; title: string; search?: string; learning?: boolean }
export interface CourseSection {
  id: string;
  title: string;
  x: number;
  y: number;
  items: CatalogItem[];
  tasks: string[];
  entry: string;
}
export interface CourseMap { sections: CourseSection[]; edges: [string, string][] }

export function agentMap(course: any): CourseMap {
  const layout = [
    ['basics', 0, 220], ['tools', 340, 220], ['graph', 340, 0],
    ['retrieval', 680, 440], ['runtime', 680, 220],
    ['sessions', 1020, 0], ['project', 1360, 220],
  ] as const;
  return {
    sections: course.groups.map((title: string, index: number) => {
      const [id, x, y] = layout[index];
      const chapters = course.chapters.filter((chapter: any) => chapter.group === title);
      return {
        id, title, x, y,
        items: chapters.map((chapter: any) => ({
          id: chapter.id, title: chapter.title,
          search: [chapter.file, chapter.interface?.function, chapter.success, ...(chapter.documentedImports || [])].join(' '),
        })),
        tasks: chapters.map((chapter: any) => chapter.id), entry: chapters[0].id,
      };
    }),
    edges: [
      ['basics', 'tools'], ['basics', 'graph'], ['basics', 'retrieval'],
      ['tools', 'retrieval'], ['tools', 'runtime'], ['graph', 'sessions'],
      ['runtime', 'sessions'], ['retrieval', 'project'], ['sessions', 'project'],
    ],
  };
}

export function pytorchMap(course: any): CourseMap {
  const positions: Record<string, [number, number]> = {
    tensor: [0, 220], shape: [340, 220], data: [680, 0],
    training: [680, 440], attention: [1020, 220], llm: [1360, 220],
  };
  return {
    sections: course.modules.map((module: any) => {
      const tasks = course.problems.filter((problem: any) => problem.moduleId === module.id && (!problem.kind || problem.kind === 'problem'));
      const [x, y] = positions[module.id];
      return {
        id: module.id, title: module.title, x, y, entry: 'module:' + module.id,
        tasks: tasks.map((problem: any) => problem.id),
        items: [
          { id: 'module:' + module.id, title: '函数学习', learning: true, search: module.lessons.map((lesson: any) => lesson.name).join(' ') },
          ...tasks.map((problem: any) => ({ id: problem.id, title: problem.title, search: problem.id + ' ' + problem.signature })),
        ],
      };
    }),
    edges: [
      ['tensor', 'shape'], ['shape', 'data'], ['shape', 'training'],
      ['shape', 'attention'], ['training', 'attention'], ['data', 'llm'], ['attention', 'llm'],
    ],
  };
}

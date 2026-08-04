type Props = { text: string };

export function ScreenLabel({ text }: Props) {
  return <span className="screen-label">{text}</span>;
}

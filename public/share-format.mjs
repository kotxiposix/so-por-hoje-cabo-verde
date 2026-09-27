export function formatGroupDateLine(isoDate, weekday) {
  const date = new Date(`${isoDate}T00:00:00`);
  const shortWeekday = weekday.replace("-feira", "");
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("pt-PT", { month: "long" });
  const capitalizedMonth = month.charAt(0).toUpperCase() + month.slice(1);
  return `${shortWeekday}, ${day} de ${capitalizedMonth} de ${date.getFullYear()}`;
}

export function composeGroupMessage(daily) {
  const header = [
    "BOM DIA GUERREIROS",
    "MEDITAÇÃO DO DIA",
    formatGroupDateLine(daily.date, daily.weekday),
  ].join("\n\n");
  const body = daily.body.replace("\n\n", "\n\n\n");

  return `${header}\n\n\n${daily.title}\n\n\n${body}\n\n\nSÓ POR HOJE:\n\n${daily.reflection}\n\n\nsoporhoje.cv\n\n\nFonte oficial: Narcóticos Anónimos Portugal\n© NA World Services, Inc. Reprinted by permission.`;
}

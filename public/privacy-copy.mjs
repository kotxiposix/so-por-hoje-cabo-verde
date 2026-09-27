export function getPrivacyCopy({
  accountEnabled = false,
  signedIn = false,
  syncEnabled = false,
  pushAvailable = false,
} = {}) {
  if (!accountEnabled) {
    return {
      principle: "A Jornada e a Sala Anónima ficam apenas neste dispositivo enquanto a conta segura não estiver ativa.",
      summary: "Neste ambiente, data de sobriedade, leituras, check-ins, gratidões e partilhas ficam no armazenamento do navegador. Não são enviados para uma conta nem partilhados com a equipa.",
      detail: "Ao limpar os dados do navegador ou mudar de dispositivo, estes registos podem desaparecer. Usa a exportação da Jornada para guardar uma cópia pessoal.",
      journeyIntro: "Um espaço pessoal para acompanhar a recuperação diária, sem julgamento. Os dados ficam guardados apenas neste navegador.",
      gratitudeNote: "Uma frase é suficiente. Fica guardada apenas neste dispositivo.",
      faqAnswer: "Não. Jornada, gratidões e Sala Anónima ficam apenas no dispositivo utilizado neste ambiente.",
    };
  }

  if (!signedIn) {
    return {
      principle: "A Jornada permanece neste dispositivo até entrares e escolheres explicitamente uma opção de sincronização.",
      summary: "A conta opcional está disponível, mas nenhum dado da Jornada é enviado enquanto não iniciares sessão e escolheres qual cópia queres usar.",
      detail: "Podes continuar em modo local e anónimo, exportar uma cópia pessoal ou entrar com um código por email quando quiseres sincronizar entre dispositivos.",
      journeyIntro: "Um espaço pessoal para acompanhar a recuperação diária, sem julgamento. Os dados permanecem neste navegador até escolheres sincronizá-los.",
      gratitudeNote: "Uma frase é suficiente. Permanece neste dispositivo enquanto não ativares a sincronização.",
      faqAnswer: "Não. Sem sessão e sem uma escolha de sincronização, a Jornada, as gratidões e a Sala Anónima permanecem neste dispositivo.",
    };
  }

  if (!syncEnabled) {
    return {
      principle: "A sessão está iniciada, mas a Jornada continua local até escolheres qual cópia sincronizar.",
      summary: "Entraste na conta, mas a sincronização ainda não começou. Nenhuma cópia da Jornada será enviada ou substituída antes da tua decisão.",
      detail: "No menu Mais, escolhe usar os dados deste dispositivo ou usar os dados já guardados na conta. Também podes terminar a sessão e continuar localmente.",
      journeyIntro: "A sessão está iniciada, mas os dados da Jornada continuam neste navegador até escolheres qual cópia usar.",
      gratitudeNote: "Uma frase é suficiente. Continua neste dispositivo até escolheres sincronizar a Jornada.",
      faqAnswer: "Não neste momento. A sessão está iniciada, mas nenhum dado da Jornada é sincronizado antes de escolheres qual cópia usar.",
    };
  }

  const devicePreferences = pushAvailable
    ? "A Sala Anónima continua apenas neste dispositivo. Se ativares notificações em segundo plano, a hora, o fuso horário e a subscrição técnica são tratados separadamente no servidor e não fazem parte da cópia da Jornada."
    : "A Sala Anónima e as preferências de notificação continuam apenas neste dispositivo.";
  const faqDevicePreferences = pushAvailable
    ? "A Sala Anónima continua local. As notificações em segundo plano, quando ativadas, usam um registo técnico separado da Jornada."
    : "A Sala Anónima e as preferências do dispositivo continuam locais.";

  return {
    principle: "A Jornada pode ser sincronizada com a tua conta; a Sala Anónima e as preferências deste dispositivo não entram nessa cópia.",
    summary: "Com a sincronização ativa, leituras, check-ins, gratidões, data de sobriedade e plano pessoal podem ser guardados na tua conta para uso noutros dispositivos.",
    detail: `${devicePreferences} Podes apagar a cópia da conta, terminar a sessão ou eliminar a conta no menu Mais.`,
    journeyIntro: "Um espaço pessoal para acompanhar a recuperação diária. A Jornada está ligada à tua conta e pode ser usada noutros dispositivos.",
    gratitudeNote: "Uma frase é suficiente. Com a sincronização ativa, pode ser guardada na tua conta.",
    faqAnswer: `A Jornada e as gratidões podem ser sincronizadas quando ativares essa opção. ${faqDevicePreferences}`,
  };
}

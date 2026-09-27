export function getPrivacyCopy({ accountEnabled = false, signedIn = false, syncEnabled = false } = {}) {
  if (!accountEnabled) {
    return {
      principle: "A Jornada e a Sala Anónima ficam apenas neste dispositivo enquanto a conta segura não estiver ativa.",
      summary: "Neste ambiente, data de sobriedade, leituras, check-ins, gratidões e partilhas ficam no armazenamento do navegador. Não são enviados para uma conta nem partilhados com a equipa.",
      detail: "Ao limpar os dados do navegador ou mudar de dispositivo, estes registos podem desaparecer. Usa a exportação da Jornada para guardar uma cópia pessoal.",
    };
  }

  if (!signedIn) {
    return {
      principle: "A Jornada permanece neste dispositivo até entrares e escolheres explicitamente uma opção de sincronização.",
      summary: "A conta opcional está disponível, mas nenhum dado da Jornada é enviado enquanto não iniciares sessão e escolheres qual cópia queres usar.",
      detail: "Podes continuar em modo local e anónimo, exportar uma cópia pessoal ou entrar com um código por email quando quiseres sincronizar entre dispositivos.",
    };
  }

  if (!syncEnabled) {
    return {
      principle: "A sessão está iniciada, mas a Jornada continua local até escolheres qual cópia sincronizar.",
      summary: "Entraste na conta, mas a sincronização ainda não começou. Nenhuma cópia da Jornada será enviada ou substituída antes da tua decisão.",
      detail: "No menu Mais, escolhe usar os dados deste dispositivo ou usar os dados já guardados na conta. Também podes terminar a sessão e continuar localmente.",
    };
  }

  return {
    principle: "A Jornada pode ser sincronizada com a tua conta; a Sala Anónima e as preferências deste dispositivo não entram nessa cópia.",
    summary: "Com a sincronização ativa, leituras, check-ins, gratidões, data de sobriedade e plano pessoal podem ser guardados na tua conta para uso noutros dispositivos.",
    detail: "A Sala Anónima e as preferências de notificação continuam apenas neste dispositivo. Podes apagar a cópia da conta, terminar a sessão ou eliminar a conta no menu Mais.",
  };
}
